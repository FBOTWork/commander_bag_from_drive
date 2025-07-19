#!/usr/bin/env python2
# -*- coding: utf-8 -*-

"""
Script GENÉRICO para extrair tarefas de uma bag.

Este script detecta a estrutura da mensagem ('subtasks' ou 'arena_state')
e gera um arquivo YAML com as tarefas.

<<<<<<< HEAD
MODIFICAÇÃO: O campo 'is_decoy' só é incluído na saída YAML se o seu
valor for False.
=======
MODIFICAÇÃO: O script agora para de ler a bag após processar a
primeira mensagem encontrada no tópico especificado.
>>>>>>> cfce05a5b567e289953da158f08dadc2b8fbfe3f
"""

import rosbag
import argparse
import yaml
import logging
import sys
import os

# --- Configuração do Logging ---
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    stream=sys.stdout,
)

def encontrar_caminho_disponivel(caminho_desejado):
    """
    Verifica se um caminho de arquivo existe. Se sim, adiciona um prefixo
    numérico até encontrar um nome de arquivo disponível.
    """
    if not os.path.exists(caminho_desejado):
        return caminho_desejado

    diretorio, nome_arquivo = os.path.split(caminho_desejado)
    nome_base, extensao = os.path.splitext(nome_arquivo)

    contador = 1
    while True:
        novo_nome = "{}_{}{}".format(contador, nome_base, extensao)
        novo_caminho = os.path.join(diretorio, novo_nome)

        if not os.path.exists(novo_caminho):
            logging.warning("O caminho '{}' já existe. Salvando como '{}'.".format(caminho_desejado, novo_caminho))
            return novo_caminho
        
        contador += 1

def processar_lista_direta(lista_de_tarefas):
    """
    Processa uma lista onde cada item já é uma tarefa completa.
    """
    transportes = []
    for tarefa in lista_de_tarefas:
        try:
            transporte = {
                'destination': tarefa.destination,
<<<<<<< HEAD
=======
                'is_decoy': tarefa.object.decoy,
>>>>>>> cfce05a5b567e289953da158f08dadc2b8fbfe3f
                'object_id': tarefa.object.object,
                'source': tarefa.source,
                'target': tarefa.object.target
            }
<<<<<<< HEAD
            # --- LÓGICA MODIFICADA ---
            # Adiciona o campo 'is_decoy' apenas se for False
            if not tarefa.object.decoy:
                transporte['is_decoy'] = False
            
=======
>>>>>>> cfce05a5b567e289953da158f08dadc2b8fbfe3f
            transportes.append(transporte)
        except AttributeError as e:
            logging.error("Falha ao ler um atributo da tarefa: {}. Tarefa ignorada.".format(e))
    return transportes

def processar_estado_arena(lista_de_workstations):
    """
    Processa uma lista de workstations para gerar tarefas.
    """
    transportes = []
    origens, destinos = [], []
    
    for ws in lista_de_workstations:
        if hasattr(ws, 'objects') and len(ws.objects) > 0:
            objetos = [{'id': o.object, 'is_decoy': o.decoy, 'target': o.target} for o in ws.objects]
            origens.append((ws.name, objetos))
        else:
            destinos.append(ws.name)

    if not origens or not destinos:
        return []
    
    objetos_flat = [(origem_nome, obj) for origem_nome, obj_list in origens for obj in obj_list]

    for idx, (origem_nome, obj_info) in enumerate(objetos_flat):
        destino_nome = destinos[idx % len(destinos)]
<<<<<<< HEAD
        
        transporte = {
            'destination': destino_nome,
            'object_id': obj_info['id'],
            'source': origem_nome,
            'target': obj_info['target']
        }
        # --- LÓGICA MODIFICADA ---
        # Adiciona o campo 'is_decoy' apenas se for False
        if not obj_info['is_decoy']:
            transporte['is_decoy'] = False
            
        transportes.append(transporte)
        
    return transportes

def extrair_tarefas_generico(caminho_bag, caminho_arquivo_saida, topico_alvo):
    """
    Função principal que analisa as mensagens da bag de forma genérica.
    """
    transportes_extraidos = []

    logging.info("Iniciando leitura do arquivo .bag: '{}'".format(caminho_bag))
    logging.info("Lendo apenas do tópico especificado: '{}'".format(topico_alvo))

    with rosbag.Bag(caminho_bag, 'r') as bag:
        if topico_alvo not in bag.get_type_and_topic_info()[1].keys():
            logging.error("ERRO: O tópico '{}' não foi encontrado na bag.".format(topico_alvo))
            return

        for topico, msg, t in bag.read_messages(topics=[topico_alvo]):
            tarefas_encontradas_na_msg = False
            
=======
        transportes.append({
            'destination': destino_nome,
            'is_decoy': obj_info['is_decoy'],
            'object_id': obj_info['id'],
            'source': origem_nome,
            'target': obj_info['target']
        })
    return transportes

def extrair_tarefas_generico(caminho_bag, caminho_arquivo_saida, topico_alvo):
    """
    Função principal que analisa as mensagens da bag de forma genérica.
    """
    transportes_extraidos = []

    logging.info("Iniciando leitura do arquivo .bag: '{}'".format(caminho_bag))
    logging.info("Lendo apenas do tópico especificado: '{}'".format(topico_alvo))

    with rosbag.Bag(caminho_bag, 'r') as bag:
        if topico_alvo not in bag.get_type_and_topic_info()[1].keys():
            logging.error("ERRO: O tópico '{}' não foi encontrado na bag.".format(topico_alvo))
            return

        for topico, msg, t in bag.read_messages(topics=[topico_alvo]):
            tarefas_encontradas_na_msg = False
            
>>>>>>> cfce05a5b567e289953da158f08dadc2b8fbfe3f
            if not hasattr(msg, '__slots__'):
                logging.warning("A mensagem do tipo '{}' não é um objeto ROS padrão. Pulando.".format(msg._type))
                continue

            for nome_campo in msg.__slots__:
                valor_campo = getattr(msg, nome_campo)
                
                if not isinstance(valor_campo, list) or not valor_campo:
                    continue

                primeiro_item = valor_campo[0]

                if hasattr(primeiro_item, 'source') and hasattr(primeiro_item, 'destination') and hasattr(primeiro_item, 'object'):
                    logging.info("Campo '{}' detectado como LISTA DE TAREFAS DIRETAS. Processando...".format(nome_campo))
                    novas_tarefas = processar_lista_direta(valor_campo)
                    if novas_tarefas:
                        transportes_extraidos.extend(novas_tarefas)
                        tarefas_encontradas_na_msg = True
                    break

                elif hasattr(primeiro_item, 'name') and hasattr(primeiro_item, 'objects'):
                    logging.info("Campo '{}' detectado como ESTADO DE ARENA. Processando...".format(nome_campo))
                    novas_tarefas = processar_estado_arena(valor_campo)
                    if novas_tarefas:
                        transportes_extraidos.extend(novas_tarefas)
                        tarefas_encontradas_na_msg = True
                    break
            
<<<<<<< HEAD
=======
            # --- MODIFICAÇÃO PRINCIPAL ---
            # Após processar a primeira mensagem (com ou sem sucesso), o loop é interrompido.
>>>>>>> cfce05a5b567e289953da158f08dadc2b8fbfe3f
            logging.info("Primeira mensagem do tópico lida. Interrompendo a leitura da bag.")
            break

    if not transportes_extraidos:
        logging.error("Nenhuma tarefa foi extraída da primeira mensagem da bag. O arquivo YAML não será gerado.")
        return
    
    diretorio_destino = os.path.dirname(caminho_arquivo_saida)
    if not os.path.exists(diretorio_destino):
        logging.info("Diretório '{}' não encontrado. Criando...".format(diretorio_destino))
        os.makedirs(diretorio_destino)
        
    caminho_final_para_salvar = encontrar_caminho_disponivel(caminho_arquivo_saida)

    logging.info("Processamento concluído. Salvando {} tarefas totais em '{}'".format(len(transportes_extraidos), caminho_final_para_salvar))
    with open(caminho_final_para_salvar, 'w') as f:
        yaml.dump(transportes_extraidos, f, default_flow_style=False)
    
    logging.info("Arquivo YAML '{}' gerado com sucesso!".format(caminho_final_para_salvar))

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Extrai tarefas da primeira mensagem de um tópico da bag e salva em YAML.")
    parser.add_argument('caminho_bag', help='Caminho completo para o arquivo .bag.')
    
    parser.add_argument(
        '--output', '-o', 
        default='/home/turtlebot/main_ws/src/work_behavior/config/atwork_commander_tasks.yaml', 
        help='Caminho completo do arquivo YAML de saída.'
    )
    
    parser.add_argument(
        '--topic', 
        default='/atwork_commander/object_task', 
        help='O tópico ROS do qual extrair as tarefas. Padrão: /atwork_commander/object_task'
    )
    
    args = parser.parse_args()

    try:
        extrair_tarefas_generico(args.caminho_bag, args.output, args.topic)
    except Exception as e:
        logging.error("Ocorreu uma falha crítica: {}".format(e))