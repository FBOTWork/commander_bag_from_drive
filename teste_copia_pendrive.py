#!/usr/bin/env python2
# -*- coding: utf-8 -*-

import os
import shutil
import time
import subprocess
from datetime import datetime
import sys
import locale

# Configurar codificação padrão para UTF-8
try:
    import imp
    imp.reload(sys)
    sys.setdefaultencoding('utf-8')
except:
    pass

# Configurar locale para UTF-8
try:
    locale.setlocale(locale.LC_ALL, 'en_US.UTF-8')
except:
    try:
        locale.setlocale(locale.LC_ALL, 'C.UTF-8')
    except:
        pass

# Configurações
DESTINO = os.path.abspath(os.path.join(os.path.dirname(__file__), 'Backup_Pendrive'))
LOG_FILE = os.path.join(DESTINO, 'log.txt')
BAG_READER_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), 'bag_reader.py'))
YAML_OUTPUT_DIR = os.path.join('/home/zap/main_ws/src/work_behavior/config')

def safe_str(s):
    """Converte string para UTF-8 de forma segura."""
    if isinstance(s, str):
        return s
    else:
        return str(s)

def safe_decode(s):
    """Decodifica string de forma segura."""
    if isinstance(s, str):
        try:
            return s.decode('utf-8', errors='replace')
        except UnicodeDecodeError:
            try:
                return s.decode('latin-1', errors='replace')
            except:
                return s.decode('ascii', errors='replace')
    return s

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
        # Tratar a saída como string simples
        if isinstance(output, bytes):
            output = output.decode('ascii', errors='ignore')
        
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
        
        # Listar arquivos de forma segura
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
                
                # Copiar apenas arquivos .bag
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
        nome_saida = os.path.splitext(os.path.basename(bag_path))[0] + "_tasks.yaml"
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
            if isinstance(stdout, bytes):
                stdout = stdout.decode('ascii', errors='ignore')
            log("Saída:\n" + safe_str(stdout))
        if stderr:
            if isinstance(stderr, bytes):
                stderr = stderr.decode('ascii', errors='ignore')
            log("Erros:\n" + safe_str(stderr))

        return processo.returncode == 0
    except Exception as e:
        log("Falha ao processar .bag: " + str(e))
        return False

def log(mensagem):
    """Registra mensagens com timestamp."""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    # Garantir que a mensagem está em formato seguro
    safe_mensagem = safe_str(mensagem)
    log_entry = "[" + str(timestamp) + "] " + safe_mensagem

    try:
        with open(LOG_FILE, 'a') as f:
            f.write(log_entry + '\n')
        print(log_entry)
    except Exception as e:
        # Fallback para caracteres problemáticos
        try:
            with open(LOG_FILE, 'a') as f:
                f.write("[" + str(timestamp) + "] Erro de codificação na mensagem\n")
            print("[" + str(timestamp) + "] Erro de codificação na mensagem")
        except:
            pass

def main():
    makedirs_exist_ok(DESTINO)
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