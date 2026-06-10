# -*- coding: utf-8 -*-

"""
Venus Café - Módulo de Gestão de Análises (Solo, Folha, etc.)
=============================================================

Este módulo permite o registo, consulta, edição e exclusão de dados de 
análises laboratoriais, essenciais para a agricultura de precisão.
"""

import sqlite3
import logging
from modulos import ui
from database import executar_query

def menu_analises(usuario: dict, db_path: str, contexto_pai: list):
    """Exibe o menu principal para o módulo de Análises."""
    contexto = contexto_pai + ["Análises"]
    while True:
        ui.limpar_tela()
        ui.mostrar_logo("Gestão de Análises", contexto=contexto)
        print("\n[1] Registrar Nova Análise")
        print("[2] Consultar Histórico de Análises")
        if usuario["perfil"] == "admin":
            print("[3] Editar Análise")
            print("[4] Excluir Análise")
        print("[0] Voltar")

        opcao = input("\n>>> Selecione: ").strip()
        if opcao == '1':
            registrar_nova_analise(db_path, contexto)
        elif opcao == '2':
            consultar_historico_analises(db_path, contexto)
        elif opcao == '3' and usuario["perfil"] == "admin":
            editar_analise(db_path, contexto)
        elif opcao == '4' and usuario["perfil"] == "admin":
            excluir_analise(db_path, contexto)
        elif opcao == '0':
            return
        else:
            ui.mostrar_erro("Opção inválida.")

def registrar_nova_analise(db_path: str, contexto_pai: list):
    """Guia o utilizador através do processo de registo de uma análise completa."""
    contexto = contexto_pai + ["Novo Registro"]
    ui.limpar_tela()
    ui.mostrar_logo("Registrar Nova Análise", contexto=contexto)
    conn = None
    try:
        tipo = ui.selecionar_opcao_de_lista("Tipo de análise:", ["Solo", "Folha", "Água"], False)
        sub_tipo = None
        if tipo == "Solo":
            sub_tipo = ui.selecionar_opcao_de_lista("Sub-tipo de análise de solo:", ["Química", "Física", "Biológica"], True)
        data = ui.obter_data_valida("Data da coleta da amostra:")
        if not data: ui.mostrar_alerta("Data é obrigatória."); return
        selecao_talhao = ui.selecionar_entidade(db_path, "Selecione o talhão associado:", "talhoes", ['codigo', 'nome'])
        if not selecao_talhao: return
        talhao_codigo, _ = selecao_talhao
        laboratorio = input("Nome do laboratório (opcional): ").strip()
        recomendacoes = input("Recomendações gerais do laudo (opcional): ").strip()
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("BEGIN TRANSACTION;")
        query_analise = "INSERT INTO analises (tipo_analise, sub_tipo, data_coleta, talhao_codigo_associado, laboratorio, recomendacoes) VALUES (?, ?, ?, ?, ?, ?)"
        params_analise = (tipo, sub_tipo, data, talhao_codigo, laboratorio, recomendacoes)
        cursor.execute(query_analise, params_analise)
        analise_id = cursor.lastrowid
        while True:
            ui.limpar_tela()
            ui.mostrar_logo(f"Inserir Resultados para Análise #{analise_id}", contexto=contexto)
            print("Insira os dados de uma linha do laudo. Deixe o nome do parâmetro em branco para terminar.")
            parametro = input("\nParâmetro (ex: pH, Fósforo, K): ").strip()
            if not parametro: break
            valor = ui.obter_numero_positivo(f"Valor para '{parametro}': ")
            if valor is None: ui.mostrar_alerta("O valor é obrigatório."); continue
            unidade = input(f"Unidade de medida (ex: mg/dm³, %): ").strip()
            interpretacao = input(f"Interpretação (ex: Baixo, Médio, Alto): ").strip()
            query_resultado = "INSERT INTO resultados_analise (analise_id, parametro, valor, unidade_medida, interpretacao) VALUES (?, ?, ?, ?, ?)"
            params_resultado = (analise_id, parametro, valor, unidade, interpretacao)
            cursor.execute(query_resultado, params_resultado)
            ui.mostrar_sucesso(f"Parâmetro '{parametro}' adicionado.")
        conn.commit()
        ui.mostrar_sucesso("Análise e todos os seus resultados foram salvos com sucesso!")
    except Exception as e:
        if conn: conn.rollback()
        logging.error(f"Erro ao registrar análise: {e}", exc_info=True)
        ui.mostrar_erro(f"Ocorreu um erro e a operação foi cancelada: {e}")
    finally:
        if conn: conn.close()

def _visualizar_detalhes_analise(db_path: str, analise_id: int, contexto: list):
    """Função auxiliar para buscar e exibir os detalhes completos de uma única análise."""
    query_capa = "SELECT * FROM analises WHERE id = ?"
    capa = executar_query(db_path, query_capa, (analise_id,), fetch=True)
    if not capa: ui.mostrar_erro("Não foi possível encontrar os detalhes da análise."); return
    _, tipo, sub_tipo, data, talhao, lab, recs = capa[0]
    query_resultados = "SELECT parametro, valor, unidade_medida, interpretacao FROM resultados_analise WHERE analise_id = ? ORDER BY id"
    resultados = executar_query(db_path, query_resultados, (analise_id,), fetch=True)
    ui.limpar_tela(); ui.mostrar_logo(f"Detalhes da Análise #{analise_id}", contexto=contexto)
    print(f"\n{ui.Cores.CIANO}--- Informações Gerais ---{ui.Cores.RESET}")
    print(f"  Tipo de Análise: {tipo} {f'({sub_tipo})' if sub_tipo else ''}")
    print(f"  Data da Coleta: {data}"); print(f"  Talhão Associado: {talhao}"); print(f"  Laboratório: {lab or 'N/D'}"); print(f"  Recomendações: {recs or 'Nenhuma'}")
    print(f"\n{ui.Cores.CIANO}--- Resultados ---{ui.Cores.RESET}")
    if not resultados: ui.mostrar_alerta("Nenhum resultado detalhado foi registado.")
    else:
        ui.mostrar_tabela(["Parâmetro", "Valor", "Unidade", "Interpretação"], resultados, [25, 15, 15, 20])
    input("\nPressione Enter para voltar...")

def consultar_historico_analises(db_path: str, contexto_pai: list):
    """Exibe uma lista paginada de análises e permite selecionar uma para ver os detalhes."""
    contexto = contexto_pai + ["Histórico"]
    while True:
        ui.limpar_tela(); ui.mostrar_logo("Consultar Histórico de Análises", contexto=contexto)
        selecao = ui.selecionar_entidade(db_path, "Selecione uma análise para ver os detalhes:", "analises", ['id', 'data_coleta', 'tipo_analise', 'talhao_codigo_associado'])
        if not selecao: break
        analise_id, _, _, _ = selecao
        contexto_detalhe = contexto + [f"Análise #{analise_id}"]
        _visualizar_detalhes_analise(db_path, analise_id, contexto_detalhe)

def _editar_resultado_individual(db_path: str, analise_id: int):
    """Função auxiliar para selecionar e editar uma única linha de resultado."""
    where = ("analise_id = ?", [analise_id])
    selecao = ui.selecionar_entidade(db_path, "Selecione o parâmetro a editar:", "resultados_analise", ['id', 'parametro', 'valor'], where)
    if not selecao: return
    resultado_id, _, _ = selecao
    dados_atuais = executar_query(db_path, "SELECT * FROM resultados_analise WHERE id = ?", (resultado_id,), fetch=True)[0]
    print("\nDeixe em branco para manter o valor atual.")
    novo_p = input(f"Parâmetro [{dados_atuais[2]}]: ").strip() or dados_atuais[2]
    novo_v = ui.obter_numero_positivo(f"Valor [{dados_atuais[3]}]: ", permitir_vazio=True) or dados_atuais[3]
    nova_u = input(f"Unidade [{dados_atuais[4] or ''}]: ").strip() or dados_atuais[4]
    nova_i = input(f"Interpretação [{dados_atuais[5] or ''}]: ").strip() or dados_atuais[5]
    query = "UPDATE resultados_analise SET parametro=?, valor=?, unidade_medida=?, interpretacao=? WHERE id=?"
    params = (novo_p, novo_v, nova_u, nova_i, resultado_id)
    if executar_query(db_path, query, params): ui.mostrar_sucesso("Resultado atualizado!")
    else: ui.mostrar_erro("Falha ao atualizar o resultado.")

def _adicionar_resultado_individual(db_path: str, analise_id: int):
    """Função auxiliar para adicionar uma nova linha de resultado a uma análise."""
    parametro = input("\nNovo Parâmetro (ex: pH, Fósforo, K): ").strip()
    if not parametro: return
    valor = ui.obter_numero_positivo(f"Valor para '{parametro}': ")
    if valor is None: ui.mostrar_alerta("O valor é obrigatório."); return
    unidade = input(f"Unidade de medida (ex: mg/dm³, %): ").strip()
    interpretacao = input(f"Interpretação (ex: Baixo, Médio, Alto): ").strip()
    query = "INSERT INTO resultados_analise (analise_id, parametro, valor, unidade_medida, interpretacao) VALUES (?, ?, ?, ?, ?)"
    params = (analise_id, parametro, valor, unidade, interpretacao)
    if executar_query(db_path, query, params): ui.mostrar_sucesso(f"Parâmetro '{parametro}' adicionado.")
    else: ui.mostrar_erro("Falha ao adicionar resultado.")

def editar_analise(db_path: str, contexto_pai: list):
    """Função principal para editar uma análise e os seus resultados."""
    contexto = contexto_pai + ["Editar"]
    try:
        ui.limpar_tela(); ui.mostrar_logo("Editar Análise", contexto=contexto)
        selecao = ui.selecionar_entidade(db_path, "Selecione a análise que deseja editar:", "analises", ['id', 'data_coleta', 'tipo_analise'])
        if not selecao: return
        analise_id, _, _ = selecao
        
        dados_capa = executar_query(db_path, "SELECT * FROM analises WHERE id = ?", (analise_id,), fetch=True)[0]
        ui.limpar_tela(); ui.mostrar_logo(f"Editando Análise #{analise_id}", contexto=contexto)
        print("\n--- Editando Dados Gerais da Análise ---")
        print("Deixe em branco para manter o valor atual.")
        nova_data = ui.obter_data_valida(f"Data da coleta [{dados_capa[3]}]: ", default_hoje=False) or dados_capa[3]
        novo_lab = input(f"Laboratório [{dados_capa[5] or ''}]: ").strip() or dados_capa[5]
        novas_recs = input(f"Recomendações [{dados_capa[6] or ''}]: ").strip() or dados_capa[6]
        
        query_update_capa = "UPDATE analises SET data_coleta=?, laboratorio=?, recomendacoes=? WHERE id=?"
        if executar_query(db_path, query_update_capa, (nova_data, novo_lab, novas_recs, analise_id)):
            ui.mostrar_sucesso("Dados gerais da análise atualizados.")
        else: ui.mostrar_erro("Falha ao atualizar os dados gerais.")

        while True:
            _visualizar_detalhes_analise(db_path, analise_id, contexto)
            print("\n--- Gerenciar Resultados Individuais ---")
            opcao = ui.selecionar_opcao_de_lista("O que deseja fazer?", ["Adicionar Resultado", "Editar Resultado", "Concluir"])
            if not opcao or opcao == "Concluir": break
            if opcao == "Adicionar Resultado": _adicionar_resultado_individual(db_path, analise_id)
            elif opcao == "Editar Resultado": _editar_resultado_individual(db_path, analise_id)
    except Exception as e:
        logging.error(f"Erro ao editar análise: {e}", exc_info=True)
        ui.mostrar_erro(f"Ocorreu um erro inesperado: {e}")

def excluir_analise(db_path: str, contexto_pai: list):
    """Permite ao utilizador selecionar e excluir um registo de análise completo."""
    contexto = contexto_pai + ["Excluir"]
    try:
        ui.limpar_tela()
        ui.mostrar_logo("Excluir Análise", contexto=contexto)
        
        selecao = ui.selecionar_entidade(db_path, "Selecione a análise que deseja excluir:", "analises",
                                         ['id', 'data_coleta', 'tipo_analise', 'talhao_codigo_associado'])
        if not selecao: return
        analise_id, data, tipo, talhao = selecao

        ui.mostrar_alerta(f"A exclusão da análise de '{tipo}' de {data} para o talhão {talhao} é irreversível.")
        ui.mostrar_alerta("Isto apagará a análise e TODOS os seus resultados associados.")
        
        confirmacao = input("Digite 'CONFIRMAR' para prosseguir com a exclusão: ").strip()

        if confirmacao == "CONFIRMAR":
            if executar_query(db_path, "DELETE FROM analises WHERE id = ?", (analise_id,)):
                ui.mostrar_sucesso("Análise e todos os seus resultados foram excluídos!")
            else:
                ui.mostrar_erro("Falha ao excluir a análise.")
        else:
            ui.mostrar_alerta("Exclusão cancelada.")
    except Exception as e:
        logging.error(f"Erro ao excluir análise: {e}", exc_info=True)
        ui.mostrar_erro(f"Ocorreu um erro inesperado: {e}")
