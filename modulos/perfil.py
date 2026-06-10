# -*- coding: utf-8 -*-

"""
Venus Café - Módulo de Gestão do Perfil da Propriedade
======================================================

Este módulo contém as funções para gerir as informações gerais da fazenda,
como nome do proprietário, endereço e área total, e também para exibir
o dashboard de resumo da propriedade.
"""

import logging
from datetime import datetime, timedelta
import subprocess
import json
from modulos import ui
from database import executar_query

def _buscar_cotacao_cafe(db_path: str) -> str:
    """
    Busca a cotação do café e a taxa de câmbio, faz a conversão e retorna
    uma string formatada.
    """
    try:
        api_key_cotacao_res = executar_query(db_path, "SELECT valor FROM configuracoes WHERE chave = ?", ('API_KEY_COTACAO',), fetch=True)
        api_key_cambio_res = executar_query(db_path, "SELECT valor FROM configuracoes WHERE chave = ?", ('API_KEY_CAMBIO',), fetch=True)

        api_key_cotacao = api_key_cotacao_res[0][0] if api_key_cotacao_res else None
        api_key_cambio = api_key_cambio_res[0][0] if api_key_cambio_res else None

        if not api_key_cotacao or not api_key_cambio:
            return "Chaves de API não configuradas."

        # 1. Buscar cotação do Café (Alpha Vantage)
        url_cafe = f"https://www.alphavantage.co/query?function=COFFEE&interval=monthly&apikey={api_key_cotacao}"
        res_cafe = subprocess.run(["curl", "--http1.1", "-s", url_cafe], capture_output=True, text=True, check=True, timeout=60)
        dados_cafe = json.loads(res_cafe.stdout)
        preco_usd_libra = float(dados_cafe['data'][0]['value']) / 100.0
        
        # 2. Buscar taxa de câmbio (ExchangeRate-API)
        url_cambio = f"https://v6.exchangerate-api.com/v6/{api_key_cambio}/latest/USD"
        res_cambio = subprocess.run(["curl", "--http1.1", "-s", url_cambio], capture_output=True, text=True, check=True, timeout=60)
        dados_cambio = json.loads(res_cambio.stdout)
        taxa_brl_usd = float(dados_cambio['conversion_rates']['BRL'])
        
        # 3. Fazer a conversão para Reais por saca de 60kg
        preco_usd_kg = preco_usd_libra / 0.453592
        preco_usd_saca = preco_usd_kg * 60
        preco_brl_saca = preco_usd_saca * taxa_brl_usd
        
        return f"Café Arábica (ICE): R$ {preco_brl_saca:.2f} / saca | Câmbio USD: R$ {taxa_brl_usd:.2f}"

    except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
        return "Falha de conexão ao buscar cotações."
    except (KeyError, IndexError, TypeError, json.JSONDecodeError):
        info = locals().get('dados_cafe', {}).get("Information", "Resposta inválida da API.")
        return f"Erro na API de cotações: {info}"
    except Exception as e:
        logging.error(f"Erro inesperado ao buscar cotações: {e}", exc_info=True)
        return "Ocorreu um erro ao processar as cotações."

def gerenciar_perfil_agricultor(db_path: str):
    """
    Permite criar ou editar o perfil da propriedade, incluindo coordenadas e altitude.
    """
    contexto = ["Perfil", "Editar"]
    try:
        perfil = executar_query(db_path, "SELECT * FROM perfil_agricultor LIMIT 1", fetch=True)
        ui.limpar_tela()
        ui.mostrar_logo("Perfil da Propriedade", contexto=contexto)
        
        dados_atuais = {}
        id_perfil = None
        if perfil:
            print("\nEditando perfil existente:")
            p_data = perfil[0]
            id_perfil = p_data[0]
            dados_atuais = {
                'nome': p_data[1], 'propriedade': p_data[2], 'endereco': p_data[3],
                'telefone': p_data[4], 'email': p_data[5], 'area_total': p_data[6],
                'latitude': p_data[7], 'longitude': p_data[8],
                'altitude_min': p_data[9], 'altitude_max': p_data[10]
            }
        else:
            print("\nCriando novo perfil:")
            dados_atuais = {'nome': '', 'propriedade': '', 'endereco': '', 'telefone': '', 'email': '', 'area_total': 0.0, 'latitude': None, 'longitude': None, 'altitude_min': None, 'altitude_max': None}
        
        print("Deixe em branco para manter o valor atual (se houver).\n")
        nome = input(f"Nome do Agricultor [{dados_atuais.get('nome') or ''}]: ").strip() or dados_atuais.get('nome')
        propriedade = input(f"Nome da Propriedade [{dados_atuais.get('propriedade') or ''}]: ").strip() or dados_atuais.get('propriedade')
        endereco = input(f"Endereço [{dados_atuais.get('endereco') or ''}]: ").strip() or dados_atuais.get('endereco')
        telefone = input(f"Telefone [{dados_atuais.get('telefone') or ''}]: ").strip() or dados_atuais.get('telefone')
        email = input(f"Email [{dados_atuais.get('email') or ''}]: ").strip() or dados_atuais.get('email')
        area_total = ui.obter_numero_positivo(f"Área Total (ha) [{dados_atuais.get('area_total') or 0.0}]: ", permitir_vazio=True) or dados_atuais.get('area_total')

        print("\n--- Coordenadas Geográficas ---")
        latitude = ui.obter_coordenada("Latitude", 'latitude', valor_atual=dados_atuais.get('latitude'))
        longitude = ui.obter_coordenada("Longitude", 'longitude', valor_atual=dados_atuais.get('longitude'))
        
        print("\n--- Faixa de Altitude da Propriedade ---")
        alt_min = ui.obter_numero_positivo(f"Altitude Mínima (m) [{dados_atuais.get('altitude_min') or 'N/D'}]: ", permitir_vazio=True) or dados_atuais.get('altitude_min')
        alt_max = ui.obter_numero_positivo(f"Altitude Máxima (m) [{dados_atuais.get('altitude_max') or 'N/D'}]: ", permitir_vazio=True) or dados_atuais.get('altitude_max')
        
        if alt_min is not None and alt_max is not None and alt_max < alt_min:
            ui.mostrar_erro("A altitude máxima não pode ser inferior à mínima."); return

        if id_perfil:
            query = "UPDATE perfil_agricultor SET nome=?, propriedade=?, endereco=?, telefone=?, email=?, area_total=?, latitude=?, longitude=?, altitude_min=?, altitude_max=? WHERE id=?"
            params = (nome, propriedade, endereco, telefone, email, area_total, latitude, longitude, alt_min, alt_max, id_perfil)
        else:
            query = "INSERT INTO perfil_agricultor (nome, propriedade, endereco, telefone, email, area_total, latitude, longitude, altitude_min, altitude_max) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"
            params = (nome, propriedade, endereco, telefone, email, area_total, latitude, longitude, alt_min, alt_max)
        
        if executar_query(db_path, query, params): ui.mostrar_sucesso("Perfil salvo com sucesso!")
        else: ui.mostrar_erro("Erro ao salvar perfil")
    except Exception as e:
        logging.error(f"Erro ao gerenciar perfil: {e}", exc_info=True)
        ui.mostrar_erro(f"Erro ao salvar perfil: {e}")

def visualizar_perfil(db_path: str):
    """Exibe os dados do perfil da propriedade atualmente registado."""
    contexto = ["Perfil", "Visualizar"]
    try:
        perfil = executar_query(db_path, "SELECT * FROM perfil_agricultor LIMIT 1", fetch=True)
        ui.limpar_tela(); ui.mostrar_logo("Perfil da Propriedade", contexto=contexto)
        if not perfil:
            ui.mostrar_alerta("Perfil ainda não cadastrado!"); input("\nPressione Enter..."); return
        
        p_data = perfil[0]
        print(f"\n{ui.Cores.CIANO}Agricultor:{ui.Cores.RESET} {p_data[1] or 'N/D'}")
        print(f"{ui.Cores.CIANO}Propriedade:{ui.Cores.RESET} {p_data[2] or 'N/D'}")
        print(f"{ui.Cores.CIANO}Endereço:{ui.Cores.RESET} {p_data[3] or 'N/D'}")
        print(f"{ui.Cores.CIANO}Telefone:{ui.Cores.RESET} {p_data[4] or 'N/D'}")
        print(f"{ui.Cores.CIANO}Email:{ui.Cores.RESET} {p_data[5] or 'N/D'}")
        print(f"{ui.Cores.CIANO}Área Total:{ui.Cores.RESET} {p_data[6] or 0:.2f} ha")
        print(f"\n--- Localização e Altitude ---")
        print(f"{ui.Cores.CIANO}Latitude:{ui.Cores.RESET} {p_data[7] or 'Não definida'}")
        print(f"{ui.Cores.CIANO}Longitude:{ui.Cores.RESET} {p_data[8] or 'Não definida'}")
        print(f"{ui.Cores.CIANO}Faixa de Altitude:{ui.Cores.RESET} {p_data[9] or '?'}m a {p_data[10] or '?'}m")
        input("\nPressione Enter para voltar...")
    except Exception as e:
        logging.error(f"Erro ao visualizar perfil: {e}", exc_info=True)
        ui.mostrar_erro(f"Erro ao visualizar perfil: {e}")

def mostrar_resumo_propriedade(db_path: str):
    """Calcula e exibe um dashboard com os principais indicadores da fazenda e do clima."""
    contexto = ["Perfil", "Dashboard"]
    try:
        ui.limpar_tela()
        ui.mostrar_logo("Resumo da Propriedade", contexto=contexto)
        num_talhoes = executar_query(db_path, "SELECT COUNT(*) FROM talhoes", fetch=True)[0][0]
        num_plantas = executar_query(db_path, "SELECT COUNT(*) FROM plantas WHERE status = 'ativa'", fetch=True)[0][0]
        area_total_res = executar_query(db_path, "SELECT area_total FROM perfil_agricultor LIMIT 1", fetch=True)
        area_total = area_total_res[0][0] if area_total_res and area_total_res[0] else 0.0
        area_plantada_m2_res = executar_query(db_path, "SELECT SUM(l.quantidade_plantas * l.espacamento_planta * t.espacamento_linha) FROM linhas l JOIN talhoes t ON l.talhao_codigo = t.codigo", fetch=True)
        area_plantada_m2 = area_plantada_m2_res[0][0] or 0.0
        area_plantada_ha = area_plantada_m2 / 10000.0
        data_30_dias_atras = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
        query_chuva = "SELECT SUM(precipitacao_mm) FROM registros_climaticos WHERE data_leitura >= ?"
        chuva_res = executar_query(db_path, query_chuva, (data_30_dias_atras,), fetch=True)
        chuva_30_dias = chuva_res[0][0] or 0.0
        query_temp = "SELECT AVG((temperatura_min_c + temperatura_max_c) / 2.0) FROM registros_climaticos WHERE data_leitura >= ? AND temperatura_min_c IS NOT NULL AND temperatura_max_c IS NOT NULL"
        temp_res = executar_query(db_path, query_temp, (data_30_dias_atras,), fetch=True)
        temp_media_30_dias = temp_res[0][0] or 0.0
        cotacao_str = _buscar_cotacao_cafe(db_path)
        print("\n" + "="*60)
        print(f"{'DASHBOARD DA PROPRIEDADE':^60}")
        print("="*60)
        print(f"- Área Total da Propriedade: {area_total or 0:.2f} ha")
        print(f"- Área Efetivamente Plantada:  {area_plantada_ha:.2f} ha")
        print(f"- Número de Talhões:          {num_talhoes}")
        print(f"- Total de Plantas Ativas:    {num_plantas}")
        print(f"\n{ui.Cores.CIANO}--- Resumo Climático (Últimos 30 dias) ---{ui.Cores.RESET}")
        print(f"- Precipitação Acumulada:   {chuva_30_dias:.1f} mm")
        print(f"- Temperatura Média:        {temp_media_30_dias:.1f} °C")
        print(f"\n{ui.Cores.CIANO}--- Mercado ---{ui.Cores.RESET}")
        print(f" {cotacao_str}")
        print("\n" + "="*60)
        input("\nPressione Enter para voltar...")
    except Exception as e:
        logging.error(f"Erro ao gerar resumo: {e}", exc_info=True)
        ui.mostrar_erro(f"Ocorreu um erro ao gerar o resumo: {e}")
