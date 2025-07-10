#!/usr/bin/env python2
# -*- coding: utf-8 -*-

"""
Script final para ler uma bag do atwork_commander, extrair os dados
aninhados da tarefa, ignorar tarefas duplicadas e salvar cada transporte
de objeto individualmente em um arquivo YAML.

Este script foi modificado para rodar sem depender do roscore/ROS
e usa exclusivamente o método .format() para strings.
"""

import rosbag
import argparse
import yaml
import logging
import sys
import os
import shutil

# Configuração básica do logging. A string 'format' aqui usa uma sintaxe
# especial do módulo logging e não deve ser alterada para .format().
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    stream=sys.stdout,
)

class ErroLeituraBag(Exception):
    """Exceção personalizada para erros que ocorrem ao processar um arquivo de bag."""
    pass

def extrair_e_salvar_em_yaml(caminho_bag, arquivo_saida):
    """
    Lê a bag, ignora duplicatas e salva cada transporte de objeto individualmente.
    Corrigido: associa cada objeto de origem a uma workstation de destino diferente, na ordem.
    """
    topico_alvo = '/atwork_commander/task'
    logging.info("Abrindo a bag: {}".format(caminho_bag))

    transportes_individuais = []
    tarefas_vistas = set()
    
    try:
        with rosbag.Bag(caminho_bag, 'r') as bag:
            logging.info("Iniciando a extração de dados do tópico '{}'...".format(topico_alvo))
            
            for topico, msg, t in bag.read_messages(topics=[topico_alvo]):
                # Coletar workstations de origem (com objetos) e destino (sem objetos)
                origens = []  # lista de (nome, [objetos])
                destinos = [] # lista de nomes
                if hasattr(msg, 'arena_start_state'):
                    for workstation in msg.arena_start_state:
                        if hasattr(workstation, 'objects') and len(workstation.objects) > 0:
                            objetos = []
                            for obj in workstation.objects:
                                objetos.append({
                                    'id': getattr(obj, 'object', None),
                                    'is_decoy': getattr(obj, 'decoy', None)
                                })
                            origens.append((workstation.name, objetos))
                        else:
                            destinos.append(workstation.name)
                # Se não houver objetos, pula
                if not origens or not destinos:
                    continue
                # Para cada objeto, associa a um destino (na ordem)
                objetos_flat = []
                for origem_nome, objetos in origens:
                    for obj in objetos:
                        objetos_flat.append((origem_nome, obj))
                # Se houver mais objetos que destinos, faz ciclo
                for idx, (origem_nome, obj_info) in enumerate(objetos_flat):
                    destino_nome = destinos[idx % len(destinos)]
                    chave_da_tarefa = (origem_nome, destino_nome, obj_info['id'], obj_info['is_decoy'])
                    if chave_da_tarefa in tarefas_vistas:
                        continue
                    tarefas_vistas.add(chave_da_tarefa)
                    transporte = {
                        'source': origem_nome,
                        'destination': destino_nome,
                        'object_id': obj_info['id'],
                        'is_decoy': obj_info['is_decoy']
                    }
                    transportes_individuais.append(transporte)

            if not transportes_individuais:
                logging.warning("Nenhuma tarefa única foi encontrada no tópico '{}'. Nenhum arquivo será gerado.".format(topico_alvo))
                return

            logging.info("Processamento concluído. Salvando {} transportes de objeto únicos em '{}'".format(len(transportes_individuais), arquivo_saida))
            with open(arquivo_saida, 'w') as f:
                yaml.dump(transportes_individuais, f, default_flow_style=False)
            
            logging.info("Arquivo salvo com sucesso!")
            
            # Também salvar na pasta config do work_behavior
            config_path = '/home/turtlebot/main_ws/src/work_behavior/config'
            if os.path.exists(config_path):
                try:
                    config_file = os.path.join(config_path, os.path.basename(arquivo_saida))
                    shutil.copy2(arquivo_saida, config_file)
                    logging.info("Arquivo também salvo em: {}".format(config_file))
                except Exception as e:
                    logging.warning("Não foi possível salvar na pasta config: {}".format(e))
            else:
                logging.warning("Pasta config não encontrada: {}".format(config_path))

    except Exception as e:
        raise ErroLeituraBag("Falha ao processar o arquivo de bag: {}".format(e))

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Extrai tarefas únicas de uma bag e salva em um arquivo YAML, sem precisar de ROS.")
    parser.add_argument('caminho_bag', help='O caminho completo para o arquivo .bag.')
    parser.add_argument('--output', '-o', default='atwork_commander_tasks.yaml', help='Nome do arquivo YAML de saída.')
    args = parser.parse_args()

    try:
        extrair_e_salvar_em_yaml(args.caminho_bag, args.output)
        
    except ErroLeituraBag as e:
        # A exceção 'e' já é uma string formatada, então podemos imprimi-la diretamente.
        logging.error(e)
        
    except KeyboardInterrupt:
        logging.info("\nProcesso interrompido pelo usuário.")
    
    except Exception as e:
        # Alterado de f-string para .format()
        logging.error("Ocorreu um erro inesperado: {}".format(e))