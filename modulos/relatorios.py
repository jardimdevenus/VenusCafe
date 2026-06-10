# -*- coding: utf-8 -*-

"""
Venus Café - Módulo de Relatórios e Análises
===========================================

Este módulo contém a lógica para gerar relatórios consolidados a partir
dos dados registados no sistema, fornecendo insights de gestão.
"""

import logging
from modulos import ui
from database import executar_query

def _menu_relatorios_operacionais(db_path: str, usuario: dict, contexto_pai: list):
    """Sub-menu para a categoria de relatórios operacionais."""
    contexto = contexto_pai + ["Operacionais"]
    while True:
        ui.limpar_tela()
        ui.mostrar_logo("Relatórios Operacionais", contexto=contexto)
        print("\n[1] Histórico de Atividades por Colaborador")
        print("[2] Histórico Completo de um Talhão (Dossier)")
        print("[0] Voltar")
        
        opcao = input("\n>>> Selecione: ").strip()
        if opcao == '1':
            relatorio_atividades_por_colaborador(db_path, contexto)
        elif opcao == '2':
            relatorio_dossie_talhao(db_path, contexto)
        elif opcao == '0':
            return
        else:
            ui.mostrar_erro("Opção inválida.")

def _menu_relatorios_agronomicos(db_path: str, usuario: dict, contexto_pai: list):
    """Sub-menu para a categoria de relatórios agronômicos."""
    contexto = contexto_pai + ["Agronômicos"]
    while True:
        ui.limpar_tela()
        ui.mostrar_logo("Relatórios Agronômicos", contexto=contexto)
        print("\n[1] Levantamento de Plantas por Cultivar")
        print("[2] Inventário Geral de Cultivares (inclui contagem 0)") # <-- NOVA OPÇÃO
        print("[3] Resumo Climático Mensal")
        print("[0] Voltar")
        
        opcao = input("\n>>> Selecione: ").strip()
        if opcao == '1':
            relatorio_levantamento_cultivares(db_path, contexto)
        elif opcao == '2':
            # Adicione a chamada para a nova função aqui
            relatorio_inventario_de_cultivares(db_path, contexto) 
        elif opcao == '3':
            relatorio_resumo_climatico_mensal(db_path, contexto)
        elif opcao == '0':
            return
        else:
            ui.mostrar_erro("Opção inválida.")




def _menu_relatorios_financeiros(db_path: str, usuario: dict, contexto_pai: list):
    """Sub-menu para a categoria de relatórios financeiros."""
    contexto = contexto_pai + ["Financeiros"]
    while True:
        ui.limpar_tela()
        ui.mostrar_logo("Relatórios Financeiros", contexto=contexto)
        print("\n[1] Análise de Custos por Talhão")
        print("[2] Análise de Custos por Insumo")
        print("[0] Voltar")
        
        opcao = input("\n>>> Selecione: ").strip()
        if opcao == '1':
            relatorio_custos_por_talhao(db_path, contexto)
        elif opcao == '2':
            relatorio_custos_por_insumo(db_path, contexto)
        elif opcao == '0':
            return
        else:
            ui.mostrar_erro("Opção inválida.")

def menu_relatorios(usuario: dict, db_path: str, contexto_pai: list):
    """Menu principal do Módulo de Relatórios."""
    contexto = contexto_pai + ["Relatórios"]
    while True:
        ui.limpar_tela()
        ui.mostrar_logo("Relatórios & Análises", contexto=contexto)
        
        print("\n[1] Relatórios Financeiros")
        print("[2] Relatórios Operacionais")
        print("[3] Relatórios Agronômicos")
        print("[0] Voltar")
        
        opcao = input("\n>>> Selecione: ").strip()
        if opcao == '1':
            _menu_relatorios_financeiros(db_path, usuario, contexto)
        elif opcao == '2':
            _menu_relatorios_operacionais(db_path, usuario, contexto)
        elif opcao == '3':
            _menu_relatorios_agronomicos(db_path, usuario, contexto)
        elif opcao == '0':
            return
        else:
            ui.mostrar_erro("Opção inválida.")


def relatorio_custos_por_talhao(db_path: str, contexto_pai: list):
    """
    Gera um relatório de custos totais de insumos, agrupado por talhão,
    dentro de um período de tempo especificado pelo utilizador.
    """
    contexto = contexto_pai + ["Custos por Talhão"]
    ui.limpar_tela()
    ui.mostrar_logo("Relatório de Custos por Talhão", contexto=contexto)

    try:
        print("\nPor favor, defina o período para a análise de custos.")
        data_inicio = ui.obter_data_valida("Data de início (DD/MM/AAAA):", default_hoje=False)
        if not data_inicio:
            ui.mostrar_alerta("Data de início é obrigatória."); return
            
        data_fim = ui.obter_data_valida("Data de fim (DD/MM/AAAA):")
        if not data_fim:
            ui.mostrar_alerta("Data de fim é obrigatória."); return

        if data_inicio > data_fim:
            ui.mostrar_erro("A data de início não pode ser posterior à data de fim."); return

        # Query que soma os custos e conta as atividades por talhão no período
        query = """
        SELECT
            talhao_codigo,
            SUM(custo_total),
            COUNT(id)
        FROM
            registros_atividades
        WHERE
            custo_total > 0
            AND data BETWEEN ? AND ?
        GROUP BY
            talhao_codigo
        ORDER BY
            SUM(custo_total) DESC
        """
        params = (data_inicio, data_fim)
        dados_relatorio = executar_query(db_path, query, params, fetch=True)
        
        ui.limpar_tela()
        ui.mostrar_logo(f"Custos por Talhão ({data_inicio} a {data_fim})", contexto=contexto)

        if not dados_relatorio:
            ui.mostrar_alerta("Nenhum custo com insumos registado no período selecionado."); return
        
        # Formata os dados para exibição na tabela
        dados_formatados = []
        custo_geral = 0
        for talhao, custo_sum, num_atividades in dados_relatorio:
            custo_geral += custo_sum
            dados_formatados.append(
                [talhao, f"R$ {custo_sum:.2f}", num_atividades]
            )
        
        cabecalhos = ["Talhão", "Custo Total (R$)", "Nº de Atividades"]
        larguras = [20, 25, 20]
        ui.mostrar_tabela(cabecalhos, dados_formatados, larguras)

        print("\n" + "="*70)
        print(f"CUSTO TOTAL NO PERÍODO: {ui.Cores.VERDE}R$ {custo_geral:.2f}{ui.Cores.RESET}")
        print("="*70)

        input("\nPressione Enter para voltar...")

    except Exception as e:
        logging.error(f"Erro ao gerar relatório de custos: {e}", exc_info=True)
        ui.mostrar_erro(f"Ocorreu um erro inesperado ao gerar o relatório: {e}")


def relatorio_custos_por_insumo(db_path: str, contexto_pai: list):
    """
    Gera um relatório de custos totais e quantidades, agrupado por insumo,
    dentro de um período de tempo especificado pelo utilizador.
    """
    contexto = contexto_pai + ["Custos por Insumo"]
    ui.limpar_tela()
    ui.mostrar_logo("Relatório de Custos por Insumo", contexto=contexto)

    try:
        print("\nPor favor, defina o período para a análise de custos.")
        data_inicio = ui.obter_data_valida("Data de início (DD/MM/AAAA):", default_hoje=False)
        if not data_inicio:
            ui.mostrar_alerta("Data de início é obrigatória."); return
            
        data_fim = ui.obter_data_valida("Data de fim (DD/MM/AAAA):")
        if not data_fim:
            ui.mostrar_alerta("Data de fim é obrigatória."); return

        if data_inicio > data_fim:
            ui.mostrar_erro("A data de início não pode ser posterior à data de fim."); return

        # Query que soma custos e quantidades por insumo no período
        query = """
        SELECT
            i.nome,
            i.unidade_medida,
            SUM(ra.quantidade_insumo),
            SUM(ra.custo_total),
            COUNT(ra.id)
        FROM
            registros_atividades ra
        JOIN
            insumos i ON ra.insumo_id = i.id
        WHERE
            ra.custo_total IS NOT NULL AND ra.custo_total > 0
            AND date(ra.data) BETWEEN ? AND ?
        GROUP BY
            i.nome
        ORDER BY
            SUM(ra.custo_total) DESC
        """
        params = (data_inicio, data_fim)
        dados_relatorio = executar_query(db_path, query, params, fetch=True)
        
        ui.limpar_tela()
        ui.mostrar_logo(f"Custos por Insumo ({data_inicio} a {data_fim})", contexto=contexto)

        if not dados_relatorio:
            ui.mostrar_alerta("Nenhum custo com insumos registado no período selecionado."); return
        
        dados_formatados = []
        custo_geral = 0
        for nome, unidade, qtd_total, custo_total, num_apps in dados_relatorio:
            if custo_total:
                custo_geral += custo_total
                dados_formatados.append(
                    [nome, f"{qtd_total or 0:.2f} {unidade}", num_apps, f"R$ {custo_total:.2f}"]
                )
        
        cabecalhos = ["Insumo", "Quantidade Total Aplicada", "Nº de Aplicações", "Custo Total (R$)"]
        larguras = [25, 28, 18, 20]
        ui.mostrar_tabela(cabecalhos, dados_formatados, larguras)

        print("\n" + "="*98)
        print(f"CUSTO TOTAL COM INSUMOS NO PERÍODO: {ui.Cores.VERDE}R$ {custo_geral:.2f}{ui.Cores.RESET}")
        print("="*98)

        input("\nPressione Enter para voltar...")

    except Exception as e:
        logging.error(f"Erro ao gerar relatório de custos por insumo: {e}", exc_info=True)
        ui.mostrar_erro(f"Ocorreu um erro inesperado ao gerar o relatório: {e}")


def relatorio_atividades_por_colaborador(db_path: str, contexto_pai: list):
    """
    Gera um relatório paginado de todas as atividades realizadas por um
    colaborador específico, dentro de um período de tempo.
    """
    contexto = contexto_pai + ["Atividades por Colaborador"]
    ui.limpar_tela()
    ui.mostrar_logo("Relatório de Atividades por Colaborador", contexto=contexto)

    try:
        # 1. Selecionar o colaborador
        selecao_colab = ui.selecionar_entidade(db_path, "Selecione o colaborador:", "colaboradores", ['id', 'nome_completo'])
        if not selecao_colab:
            return
        colaborador_id, nome_colaborador = selecao_colab

        # 2. Definir o período
        print("\nDefina o período para a análise.")
        data_inicio = ui.obter_data_valida("Data de início:", default_hoje=False)
        if not data_inicio: ui.mostrar_alerta("Data de início é obrigatória."); return
        data_fim = ui.obter_data_valida("Data de fim:")
        if not data_fim: ui.mostrar_alerta("Data de fim é obrigatória."); return
        if data_inicio > data_fim: ui.mostrar_erro("A data de início não pode ser posterior à de fim."); return

        # 3. Usar a navegação paginada para exibir os resultados
        titulo_relatorio = f"Atividades de {nome_colaborador}"
        where_clause = ("ra.colaborador_id = ? AND date(ra.data) BETWEEN ? AND ?", [colaborador_id, data_inicio, data_fim])
        
        cabecalhos = ["Data", "Tipo de Atividade", "Talhão", "Insumo", "Custo (R$)"]
        larguras = [12, 25, 10, 20, 15]
        colunas_db = [
            "date(ra.data)",
            "ta.nome",
            "ra.talhao_codigo",
            "i.nome",
            "ra.custo_total"
        ]
        join_clause = """
        JOIN tipos_atividades ta ON ra.tipo_id = ta.id
        LEFT JOIN insumos i ON ra.insumo_id = i.id
        """

        ui.navegacao_paginada(
            db_path, contexto, titulo_relatorio, "registros_atividades ra",
            cabecalhos, larguras, colunas_db,
            join_clause=join_clause,
            where_clause=where_clause,
            order_by_clause="ra.data DESC"
        )

    except Exception as e:
        logging.error(f"Erro ao gerar relatório de atividades por colaborador: {e}", exc_info=True)
        ui.mostrar_erro(f"Ocorreu um erro inesperado ao gerar o relatório: {e}")


def relatorio_dossie_talhao(db_path: str, contexto_pai: list):
    """
    Gera um "dossier" completo para um talhão específico, consolidando
    dados de base, sumários, e históricos de atividades, análises e clima.
    """
    contexto = contexto_pai + ["Dossier do Talhão"]
    ui.limpar_tela()
    ui.mostrar_logo("Dossier Completo do Talhão", contexto=contexto)

    try:
        # 1. Selecionar o talhão
        selecao = ui.selecionar_entidade(db_path, "Selecione o talhão para gerar o dossier:", "talhoes", ['codigo', 'nome'])
        if not selecao: return
        talhao_codigo, nome_talhao = selecao
        
        # 2. Definir o período para os históricos
        print("\nDefina o período para o histórico de atividades e clima.")
        data_inicio = ui.obter_data_valida("Data de início:", default_hoje=False)
        if not data_inicio: ui.mostrar_alerta("Data de início é obrigatória."); return
        data_fim = ui.obter_data_valida("Data de fim:")
        if not data_fim: ui.mostrar_alerta("Data de fim é obrigatória."); return
        if data_inicio > data_fim: ui.mostrar_erro("A data de início não pode ser posterior à de fim."); return

        # 3. Buscar todas as informações de diferentes tabelas
        dados_talhao = executar_query(db_path, "SELECT * FROM talhoes WHERE codigo = ?", (talhao_codigo,), fetch=True)[0]
        sumario_linhas = executar_query(db_path, "SELECT COUNT(*) FROM linhas WHERE talhao_codigo = ?", (talhao_codigo,), fetch=True)[0][0]
        sumario_plantas = executar_query(db_path, "SELECT COUNT(p.id) FROM plantas p JOIN linhas l ON p.linha_id = l.id WHERE l.talhao_codigo = ? AND p.status = 'ativa'", (talhao_codigo,), fetch=True)[0][0]
        
        query_atividades = "SELECT date(data), (SELECT nome FROM tipos_atividades WHERE id=tipo_id) FROM registros_atividades WHERE talhao_codigo = ? AND date(data) BETWEEN ? AND ? ORDER BY data DESC LIMIT 5"
        ultimas_atividades = executar_query(db_path, query_atividades, (talhao_codigo, data_inicio, data_fim), fetch=True)
        
        query_clima = "SELECT SUM(precipitacao_mm), AVG((temperatura_min_c + temperatura_max_c) / 2.0) FROM registros_climaticos WHERE date(data_leitura) BETWEEN ? AND ?"
        resumo_clima = executar_query(db_path, query_clima, (data_inicio, data_fim), fetch=True)[0]

        # 4. Exibir o Dossier consolidado
        ui.limpar_tela()
        ui.mostrar_logo(f"Dossier do Talhão: {nome_talhao}", contexto=contexto)
        
        print(f"\n{ui.Cores.CIANO}--- DADOS DE BASE ---{ui.Cores.RESET}")
        print(f"  Código: {dados_talhao[0]} | Espaçamento: {dados_talhao[4]}m | Altitude Média: {dados_talhao[7] or 'N/D'}m")
        print(f"  Cultivar Padrão: {dados_talhao[6] or 'Nenhum'}")
        
        print(f"\n{ui.Cores.CIANO}--- SUMÁRIO ATUAL ---{ui.Cores.RESET}")
        print(f"  Nº de Linhas: {sumario_linhas} | Nº de Plantas Ativas: {sumario_plantas}")
        
        print(f"\n{ui.Cores.CIANO}--- ÚLTIMAS 5 ATIVIDADES NO PERÍODO ({data_inicio} a {data_fim}) ---{ui.Cores.RESET}")
        if ultimas_atividades:
            for data, tipo in ultimas_atividades:
                print(f"  - {ui.datetime.strptime(data, '%Y-%m-%d').strftime('%d/%m/%Y')}: {tipo}")
        else:
            print("  - Nenhuma atividade registrada no período.")

        print(f"\n{ui.Cores.CIANO}--- RESUMO CLIMÁTICO NO PERÍODO ---{ui.Cores.RESET}")
        if resumo_clima and resumo_clima[0] is not None:
            print(f"  - Precipitação Acumulada: {resumo_clima[0]:.1f} mm")
            print(f"  - Temperatura Média: {resumo_clima[1]:.1f} °C")
        else:
            print("  - Nenhum dado climático registrado no período.")

        input("\n\nPressione Enter para voltar...")

    except Exception as e:
        logging.error(f"Erro ao gerar dossier do talhão: {e}", exc_info=True)
        ui.mostrar_erro(f"Ocorreu um erro inesperado ao gerar o relatório: {e}")


def relatorio_levantamento_cultivares(db_path: str, contexto_pai: list):
    """
    Gera um relatório de inventário de plantas, agrupado por cultivar e talhão.
    """
    contexto = contexto_pai + ["Levantamento por Cultivar"]
    titulo_relatorio = "Levantamento de Plantas por Cultivar"
    join_clause = """
    JOIN linhas l ON p.linha_id = l.id
    JOIN talhoes t ON l.talhao_codigo = t.codigo
    JOIN cultivares c ON p.cultivar_codigo = c.codigo
    """
    where_clause = ("p.status = 'ativa' AND p.cultivar_codigo IS NOT NULL", [])

    cabecalhos = ["Cultivar", "Talhão", "Nº de Plantas Ativas"]
    larguras = [30, 30, 20]
    colunas_db = ["c.nome", "t.nome", "COUNT(p.id)"]
    
    group_by_clause = "c.nome, t.nome"
    order_by_clause = "c.nome ASC, t.nome ASC"

    ui.navegacao_paginada(
        db_path, contexto, titulo_relatorio, "plantas p",
        cabecalhos, larguras, colunas_db,
        join_clause=join_clause,
        where_clause=where_clause,
        group_by_clause=group_by_clause,
        order_by_clause=order_by_clause
    )

def relatorio_inventario_de_cultivares(db_path: str, contexto_pai: list):
    """
    Gera um relatório de inventário de TODAS as cultivares, mostrando quantas
    plantas ativas estão associadas a cada uma, incluindo as que não têm nenhuma.
    """
    contexto = contexto_pai + ["Inventário de Cultivares"]
    titulo_relatorio = "Inventário Geral de Cultivares"
    
    # A consulta SQL é a chave aqui. Usamos LEFT JOIN.
    join_clause = """
    LEFT JOIN plantas p ON c.codigo = p.cultivar_codigo AND p.status = 'ativa'
    """
    
    cabecalhos = ["Código", "Nome da Cultivar", "Nº de Plantas Ativas"]
    larguras = [10, 35, 25]
    colunas_db = ["c.codigo", "c.nome", "COUNT(p.id)"]
    
    # O group_by_clause é essencial para a contagem funcionar corretamente
    group_by_clause = "c.codigo, c.nome"
    order_by_clause = "c.nome ASC"

    # Chamamos a função de paginação, começando da tabela 'cultivares'
    ui.navegacao_paginada(
        db_path, contexto, titulo_relatorio, "cultivares c",
        cabecalhos, larguras, colunas_db,
        join_clause=join_clause,
        group_by_clause=group_by_clause,
        order_by_clause=order_by_clause
    )



def relatorio_resumo_climatico_mensal(db_path: str, contexto_pai: list):
    """
    Gera um relatório climático consolidado para um mês e ano específicos
    informados pelo utilizador.
    """
    contexto = contexto_pai + ["Resumo Climático Mensal"]
    ui.limpar_tela()
    ui.mostrar_logo("Relatório Climático Mensal", contexto=contexto)

    try:
        # 1. Coletar o ano e o mês do utilizador
        ano_atual = ui.datetime.now().year
        mes_atual = ui.datetime.now().month
        
        ano = ui.obter_numero_positivo(f"Insira o ano (ex: {ano_atual}): ", tipo_dado=int)
        if not ano: ui.mostrar_alerta("Ano é obrigatório."); return

        mes = ui.obter_numero_positivo(f"Insira o mês (1-12) [{mes_atual}]: ", tipo_dado=int, permitir_vazio=True) or mes_atual
        if not (1 <= mes <= 12):
            ui.mostrar_erro("Mês inválido. Deve ser um número entre 1 e 12."); return

        # Formata o período para a consulta SQL (ex: '2025-08')
        periodo = f"{ano}-{mes:02d}"

        # 2. Query que calcula os agregados para o mês
        query = """
        SELECT
            SUM(precipitacao_mm),
            AVG((temperatura_min_c + temperatura_max_c) / 2.0),
            MAX(temperatura_max_c),
            MIN(temperatura_min_c)
        FROM
            registros_climaticos
        WHERE
            strftime('%Y-%m', data_leitura) = ?
        """
        params = (periodo,)
        dados_clima = executar_query(db_path, query, params, fetch=True)
        
        if not dados_clima or dados_clima[0][0] is None:
            ui.mostrar_alerta(f"Nenhum dado climático encontrado para o período de {periodo}.")
            return
            
        chuva_total, temp_media, temp_max, temp_min = dados_clima[0]

        # 3. Exibir o resumo
        ui.limpar_tela()
        ui.mostrar_logo(f"Resumo Climático para {mes:02d}/{ano}", contexto=contexto)
        
        print("\n" + "="*50)
        print(f"{'INDICADORES CLIMÁTICOS DO PERÍODO':^50}")
        print("="*50)
        
        print(f"\n- Precipitação Acumulada no Mês: {chuva_total or 0:.1f} mm")
        print(f"- Temperatura Média Mensal:      {temp_media or 0:.1f} °C")
        print(f"- Temperatura Máxima Absoluta:   {temp_max or 0:.1f} °C")
        print(f"- Temperatura Mínima Absoluta:   {temp_min or 0:.1f} °C")
        
        print("\n" + "="*50)
        input("\nPressione Enter para voltar...")

    except Exception as e:
        logging.error(f"Erro ao gerar relatório climático mensal: {e}", exc_info=True)
        ui.mostrar_erro(f"Ocorreu um erro inesperado ao gerar o relatório: {e}")
 