# -*- coding: utf-8 -*-

"""
Venus Café - Módulo de Gestão de Dados Climáticos
"""

import sqlite3
import logging
import requests
import subprocess
import json
from datetime import datetime, timedelta
from modulos import ui
from database import executar_query

def menu_clima(usuario: dict, db_path: str, contexto_pai: list):
    """Exibe o menu principal para o módulo de Clima & Ambiente."""
    contexto = contexto_pai + ["Clima & Ambiente"]
    while True:
        ui.limpar_tela()
        ui.mostrar_logo("Clima & Ambiente", contexto=contexto)
        print("\n[1] Registrar Dados Manuais")
        print("[2] Consultar Histórico")
        print("[3] Editar Registro")
        print("[4] Sincronizar Dados do Dia Anterior via API")
        print("[0] Voltar")
        opcao = input("\n>>> Selecione: ").strip()
        if opcao == '1': registrar_dados_manuais(db_path, contexto)
        elif opcao == '2': consultar_historico_climatico(db_path, contexto)
        elif opcao == '3': editar_dados_climaticos(db_path, contexto)
        elif opcao == '4': buscar_dados_api(db_path)
        elif opcao == '0': return
        else: ui.mostrar_erro("Opção inválida.")

def registrar_dados_manuais(db_path: str, contexto_pai: list):
    """Apresenta um formulário para o registo manual de dados climáticos de um dia."""
    contexto = contexto_pai + ["Registro Manual"]
    ui.limpar_tela()
    ui.mostrar_logo("Registro Manual de Clima", contexto=contexto)
    data = ui.obter_data_valida("Data da leitura")
    if not data: ui.mostrar_alerta("Operação cancelada."); return
    try:
        dados_existentes = executar_query(db_path, "SELECT * FROM registros_climaticos WHERE data_leitura = ?", (data,), fetch=True)
        if dados_existentes:
            ui.mostrar_alerta(f"Já existe um registro para a data {data}.")
            if ui.selecionar_opcao_de_lista("Deseja atualizar?", ["Sim", "Não"], False) == "Não": return
        print("\nInsira os dados (deixe em branco se não houver medição):")
        precipitacao = ui.obter_numero_positivo("Precipitação (mm): ", permitir_vazio=True)
        temp_min = ui.obter_numero_decimal("Temperatura Mínima (°C): ")
        temp_max = ui.obter_numero_decimal("Temperatura Máxima (°C): ")
        if temp_min is not None and temp_max is not None and temp_max < temp_min:
            ui.mostrar_erro("A temperatura máxima não pode ser inferior à mínima."); return
        if dados_existentes:
            query = "UPDATE registros_climaticos SET precipitacao_mm=?, temperatura_min_c=?, temperatura_max_c=?, fonte='MANUAL' WHERE data_leitura=?"
            params = (precipitacao, temp_min, temp_max, data)
            msg = "Registro climático atualizado!"
        else:
            query = "INSERT INTO registros_climaticos (data_leitura, precipitacao_mm, temperatura_min_c, temperatura_max_c, fonte) VALUES (?, ?, ?, ?, 'MANUAL')"
            params = (data, precipitacao, temp_min, temp_max)
            msg = "Registro climático salvo!"
        if executar_query(db_path, query, params): ui.mostrar_sucesso(msg)
        else: ui.mostrar_erro("Falha ao salvar o registro.")
    except Exception as e:
        logging.error(f"Erro ao registrar dados climáticos: {e}", exc_info=True)
        ui.mostrar_erro(f"Ocorreu um erro: {e}")

def consultar_historico_climatico(db_path: str, contexto_pai: list):
    """
    Exibe uma lista paginada do histórico de dados climáticos, ordenada pela
    data mais recente.
    """
    contexto = contexto_pai + ["Histórico"]
    
    ui.navegacao_paginada(
        db_path, 
        contexto, 
        "Histórico Climático",
        "registros_climaticos",
        cabecalhos=["Data", "Precip. (mm)", "Temp. Mín (°C)", "Temp. Máx (°C)", "Umidade (%)", "Fonte"],
        larguras=[12, 15, 15, 15, 12, 10],
        colunas_db=['data_leitura', 'precipitacao_mm', 'temperatura_min_c', 'temperatura_max_c', 'umidade_relativa_percent', 'fonte'],
        order_by_clause="data_leitura DESC"
    )


def editar_dados_climaticos(db_path: str, contexto_pai: list):
    """Permite ao utilizador selecionar e editar um registo climático existente."""
    contexto = contexto_pai + ["Editar Registro"]
    try:
        ui.limpar_tela()
        ui.mostrar_logo("Editar Registro Climático", contexto=contexto)
        selecao = ui.selecionar_entidade(db_path, "Selecione a data do registro a editar:", "registros_climaticos", ['id', 'data_leitura', 'fonte'])
        if not selecao: return
        registro_id, data_leitura, fonte_atual = selecao
        dados_atuais = executar_query(db_path, "SELECT precipitacao_mm, temperatura_min_c, temperatura_max_c FROM registros_climaticos WHERE id = ?", (registro_id,), fetch=True)
        if not dados_atuais: ui.mostrar_erro("Não foi possível encontrar os detalhes."); return
        prec_atual, tmin_atual, tmax_atual = dados_atuais[0]
        ui.limpar_tela()
        ui.mostrar_logo(f"Editando Dados de {data_leitura}", contexto=contexto)
        print(f"Fonte do registro original: {fonte_atual}")
        print("\nDeixe em branco para manter o valor atual.")
        nova_prec = ui.obter_numero_positivo(f"Precipitação (mm) [{prec_atual}]: ", permitir_vazio=True) or prec_atual
        novo_tmin = ui.obter_numero_decimal(f"Temp. Mínima (°C) [{tmin_atual}]: ", valor_atual=tmin_atual)
        novo_tmax = ui.obter_numero_decimal(f"Temp. Máxima (°C) [{tmax_atual}]: ", valor_atual=tmax_atual)
        if novo_tmin is not None and novo_tmax is not None and novo_tmax < novo_tmin:
            ui.mostrar_erro("A temperatura máxima não pode ser inferior à mínima."); return
        query = "UPDATE registros_climaticos SET precipitacao_mm = ?, temperatura_min_c = ?, temperatura_max_c = ? WHERE id = ?"
        params = (nova_prec, novo_tmin, novo_tmax, registro_id)
        if executar_query(db_path, query, params): ui.mostrar_sucesso("Registro atualizado!")
        else: ui.mostrar_erro("Falha ao atualizar o registro.")
    except Exception as e:
        logging.error(f"Erro ao editar dados climáticos: {e}", exc_info=True)
        ui.mostrar_erro(f"Ocorreu um erro: {e}")

def buscar_dados_api(db_path: str):
    """
    Busca dados climáticos do dia anterior via API, com opção de sobrescrever
    dados manuais existentes.
    """
    import subprocess
    import json

    contexto = ["Ferramentas Avançadas", "Clima", "Sincronizar API"]
    ui.limpar_tela()
    ui.mostrar_logo("Sincronização via API", contexto=contexto)
    print("\nA buscar dados climáticos do dia anterior...")
    try:
        perfil = executar_query(db_path, "SELECT latitude, longitude FROM perfil_agricultor LIMIT 1", fetch=True)
        if not perfil or not perfil[0][0] or not perfil[0][1]:
            ui.mostrar_erro("Latitude e Longitude não definidas.");
            ui.mostrar_alerta("Por favor, edite o 'Perfil da Propriedade'."); return
            
        latitude, longitude = perfil[0]
        data_ontem = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
        dados_existentes = executar_query(db_path, "SELECT id, fonte FROM registros_climaticos WHERE data_leitura = ?", (data_ontem,), fetch=True)
        is_update = False
        if dados_existentes:
            fonte = dados_existentes[0][1]
            ui.mostrar_alerta(f"Já existem dados para {data_ontem} (fonte: {fonte}).")
            if ui.selecionar_opcao_de_lista("Deseja sobrescrever com os dados da API?", ["Sim", "Não"], False) == "Não":
                return
            is_update = True
        
        print(f"A consultar API para Lat: {latitude}, Lon: {longitude}...")
        url_api = (
            f"https://api.open-meteo.com/v1/forecast?latitude={latitude}&longitude={longitude}"
            f"&daily=temperature_2m_max,temperature_2m_min,precipitation_sum,relative_humidity_2m_mean"
            f"&timezone=America/Sao_Paulo&start_date={data_ontem}&end_date={data_ontem}"
        )
        comando_curl = ["curl", "-s", url_api]
        resultado = subprocess.run(comando_curl, capture_output=True, text=True, check=True, timeout=20)
        dados = json.loads(resultado.stdout)
        
        if 'error' in dados and dados['error']:
            ui.mostrar_erro(f"A API retornou um erro: {dados.get('reason', 'Erro desconhecido')}"); return
        if 'daily' not in dados or not dados['daily'].get('time'):
            ui.mostrar_erro("A resposta da API não continha dados diários."); return
        
        prec = dados['daily']['precipitation_sum'][0]
        tmax = dados['daily']['temperature_2m_max'][0]
        tmin = dados['daily']['temperature_2m_min'][0]
        umid = dados['daily']['relative_humidity_2m_mean'][0]
        
        print(f"\n{ui.Cores.VERDE}Dados encontrados para {data_ontem}:{ui.Cores.RESET}")
        print(f"  - Precipitação: {prec} mm | Temp. Mín: {tmin} °C | Temp. Máx: {tmax} °C | Humidade: {umid} %")
        
        if ui.selecionar_opcao_de_lista("\nDeseja salvar/sobrescrever estes dados?", ["Sim", "Não"], False) == "Sim":
            if is_update:
                query = "UPDATE registros_climaticos SET precipitacao_mm=?, temperatura_min_c=?, temperatura_max_c=?, umidade_relativa_percent=?, fonte='API' WHERE data_leitura=?"
                params = (prec, tmin, tmax, umid, data_ontem)
                msg_sucesso = "Dados sobrescritos com sucesso!"
            else:
                query = "INSERT INTO registros_climaticos (data_leitura, precipitacao_mm, temperatura_min_c, temperatura_max_c, umidade_relativa_percent, fonte) VALUES (?, ?, ?, ?, ?, 'API')"
                params = (data_ontem, prec, tmin, tmax, umid)
                msg_sucesso = "Dados salvos com sucesso!"

            if executar_query(db_path, query, params): ui.mostrar_sucesso(msg_sucesso)
            else: ui.mostrar_erro("Falha ao salvar os dados.")
    except Exception as e:
        logging.error(f"Erro ao buscar dados da API: {e}", exc_info=True)
        ui.mostrar_erro(f"Ocorreu um erro inesperado: {e}")
