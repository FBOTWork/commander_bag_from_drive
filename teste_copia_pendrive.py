#!/usr/bin/env python2
# -*- coding: utf-8 -*-

import os
import shutil
import time
import subprocess
from datetime import datetime
import sys
import locale
import imp

# Compatibilidade Python3: define unicode
if sys.version_info[0] >= 3:
    unicode = str

# Configuração de encoding para Python 2.7
imp.reload(sys)
sys.setdefaultencoding('utf-8')

# Configurações
DESTINO = os.path.abspath(os.path.join(os.path.dirname(__file__), 'Backup_Pendrive'))
LOG_FILE = os.path.join(DESTINO, 'log.txt')
BAG_READER_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), 'bag_reader.py'))
YAML_OUTPUT_DIR = os.path.join('/home/turtlebot/main_ws/src/work_behavior/config/') # diretorio do robo
#YAML_OUTPUT_DIR = os.path.join('/home/husky/main_ws/src/work_behavior/config') #diretorio do meu pc para testes

def limpar_pasta_yaml():
    """Limpa todos os arquivos .yaml da pasta de saída configurada."""
    try:
        if os.path.exists(YAML_OUTPUT_DIR):
            log("Limpando pasta YAML: " + YAML_OUTPUT_DIR)
            for arquivo in os.listdir(YAML_OUTPUT_DIR):
                if arquivo.endswith('.yaml') or arquivo.endswith('.yml'):
                    caminho_arquivo = os.path.join(YAML_OUTPUT_DIR, arquivo)
                    try:
                        os.unlink(caminho_arquivo)
                        log("Removido: " + arquivo)
                    except Exception as e:
                        log("Erro ao remover " + arquivo + ": " + str(e))
        else:
            log("Pasta YAML não existe, criando: " + YAML_OUTPUT_DIR)
            os.makedirs(YAML_OUTPUT_DIR)
    except Exception as e:
        log("Erro ao limpar pasta YAML: " + str(e))

def safe_str(s):
    """Converte string para UTF-8 de forma segura."""
    if isinstance(s, str):
        return s
    elif isinstance(s, unicode):
        return s.encode('utf-8', errors='replace')
    else:
        return str(s)

def makedirs_exist_ok(path):
    """Cria diretórios se não existirem (compatível com Python 2.7)."""
    try:
        os.makedirs(path)
    except OSError:
        if not os.path.isdir(path):
            raise

def get_mounted_devices():
    """Lista dispositivos montados."""
    try:
        output = subprocess.check_output(['mount'])
        devices = []
        for line in output.split('\n'):
            if line and len(line.split()) >= 3:
                try:
                    device = line.split()[2]
                    devices.append(device)
                except:
                    continue
        return devices
    except Exception as e:
        log("Erro ao listar dispositivos:" + safe_str(str(e)))
        return []

def is_usb_device(mount_point):
    """Verifica se é um pendrive."""
    return mount_point.startswith('/media/')

def copy_files(origem, destino):
    """Copia apenas arquivos .bag removendo '(1)' dos nomes."""
    try:
        makedirs_exist_ok(destino)
        
        bag_files_found = False
        
        try:
            items = os.listdir(origem)
        except OSError as e:
            log("Erro ao listar arquivos de " + safe_str(origem) + ": " + safe_str(str(e)))
            return False
        
        for item in items:
            if item.startswith('.'):
                continue
            
            try:
                src = os.path.join(origem, item)
                
                if os.path.isfile(src) and item.lower().endswith('.bag'):
                    dst_name = item.replace("(1)", "")
                    dst = os.path.join(destino, dst_name)
                    
                    shutil.copy2(src, dst)
                    log("Copiado arquivo .bag: " + safe_str(item) + " → " + safe_str(os.path.basename(dst)))
                    bag_files_found = True
            except Exception as e:
                log("Erro ao copiar arquivo " + safe_str(item) + ": " + safe_str(str(e)))
                continue
        
        if not bag_files_found:
            log("Nenhum arquivo .bag encontrado em: " + safe_str(origem))
        
        return True
    except Exception as e:
        log("Erro na cópia: " + safe_str(str(e)))
        return False

def process_bag_file(bag_path):
    """Executa bag_reader.py no arquivo .bag."""
    try:
        makedirs_exist_ok(YAML_OUTPUT_DIR)
        # nome_saida = os.path.splitext(os.path.basename(bag_path))[0] + "_tasks.yaml"
        nome_saida = "task_list.yaml"
        yaml_saida = os.path.join(YAML_OUTPUT_DIR, nome_saida)

        log("Processando: " + os.path.basename(bag_path) + " → " + nome_saida)

        cmd = [
            'python2',
            BAG_READER_PATH,
            bag_path,
            '--output', yaml_saida
        ]
        
        processo = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = processo.communicate()
        
        if stdout:
            log("Saída:\n" + safe_str(stdout))
        if stderr:
            log("Erros:\n" + safe_str(stderr))

        return processo.returncode == 0
    except Exception as e:
        log("Falha ao processar .bag: " + str(e))
        return False

def log(mensagem):
    """Registra mensagens com timestamp."""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    safe_mensagem = safe_str(mensagem)
    log_entry = "[" + timestamp + "] " + safe_mensagem

    try:
        with open(LOG_FILE, 'a') as f:
            f.write(log_entry + '\n')
        print(log_entry)
    except Exception as e:
        try:
            with open(LOG_FILE, 'a') as f:
                f.write("[" + timestamp + "] Erro de codificação na mensagem\n")
            print("[" + timestamp + "] Erro de codificação na mensagem")
        except:
            pass

def main():
    makedirs_exist_ok(DESTINO)
    limpar_pasta_yaml()
    log("Iniciando monitoramento de pendrives...")
    
    dispositivos_anteriores = set()
    
    try:
        while True:
            dispositivos_atual = set(get_mounted_devices())
            novos = dispositivos_atual - dispositivos_anteriores
            
            for dispositivo in novos:
                if is_usb_device(dispositivo):
                    log("Pendrive detectado: " + safe_str(dispositivo))
                    pasta_backup = os.path.join(
                        DESTINO, 
                        datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
                    )
                    
                    if copy_files(dispositivo, pasta_backup):
                        log("Backup criado em: " + safe_str(pasta_backup))
                        
                        try:
                            for arquivo in os.listdir(pasta_backup):
                                if arquivo.endswith('.bag'):
                                    process_bag_file(os.path.join(pasta_backup, arquivo))
                        except Exception as e:
                            log("Erro ao processar arquivos .bag: " + safe_str(str(e)))

                    sys.exit(0)
            
            dispositivos_anteriores = dispositivos_atual
            time.sleep(5)
            
    except KeyboardInterrupt:
        log("Monitoramento interrompido")
    except Exception as e:
        log("ERRO: " + safe_str(str(e)))

if __name__ == "__main__":
    main()