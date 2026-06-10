# -*- coding: utf-8 -*-

"""
Venus Café - Módulo de Gestão de Atividades Agrícolas
=====================================================

Este módulo centraliza o registo, a consulta e a gestão de todas as
atividades agrícolas realizadas na fazenda, bem como o CRUD para os
diferentes tipos de atividades.
"""

import sqlite3
import logging
import time
import re
from datetime import datetime
from modulos import ui
from database import executar_query

def menu_atividades(usuario: dict, db_path: str):
    """Exibe o menu principal para a gestão de atividades agrícolas."""
    contexto = ["Atividades Agrícolas"]
    while True:
        ui.limpar_tela()
        ui.mostrar_logo("Atividades Agrícolas", contexto=contexto)
        
        print("\n[1] Registrar Nova Atividade")
        print("[2] Listar Atividades Registradas")
        print("[3] Gerenciar Tipos de Atividades")
        if usuario["perfil"] == "admin":
            print("[4] Excluir Atividade Registrada")
        print("[0] Voltar")
        
        opcao = input("\n>>> Selecione: ").strip()
        
        if opcao == "1": registrar_atividade(db_path, contexto)
        elif opcao == "2": listar_atividades(db_path, contexto)
        elif opcao == "3": menu_tipos_atividades(db_path, usuario, contexto)
        elif opcao == "4" and usuario["perfil"] == "admin": excluir_atividade_registrada(db_path, contexto)
        elif opcao == "0": return
        else: ui.mostrar_erro("Opção inválida!")

def _selecionar_alvo(db_path: str) -> dict:
    """Função auxiliar que guia o utilizador para selecionar o alvo de uma atividade."""
    selecao_talhao = ui.selecionar_entidade(db_path, "Selecione o Talhão:", "talhoes", ['codigo', 'nome'])
    if not selecao_talhao: return {'alvo_str': None}
    talhao_codigo, nome_talhao = selecao_talhao

    opcao = ui.selecionar_opcao_de_lista(f"\nAlvo: {nome_talhao}. Aplicar a:", ["Todo o Talhão", "Uma Linha específica"])
    if not opcao: return {'alvo_str': None}
    if opcao == "Todo o Talhão":
        return {'talhao_codigo': talhao_codigo, 'linha_id': None, 'planta_id': None, 'alvo_str': f'Todo o Talhão {nome_talhao}'}
        
    where = ("talhao_codigo = ?", [talhao_codigo])
    selecao_linha = ui.selecionar_entidade(db_path, "Selecione a Linha:", "linhas", ['id', 'numero'], where)
    if not selecao_linha: return {'alvo_str': None}
    linha_id, numero_linha = selecao_linha

    opcao = ui.selecionar_opcao_de_lista(f"\nAlvo: Linha {numero_linha}. Aplicar a:", ["Toda a Linha", "Uma Planta específica"])
    if not opcao: return {'alvo_str': None}
    if opcao == "Toda a Linha":
        return {'talhao_codigo': talhao_codigo, 'linha_id': linha_id, 'planta_id': None, 'alvo_str': f'{nome_talhao} › Linha {numero_linha}'}
    
    where = ("linha_id = ? AND status = 'ativa'", [linha_id])
    selecao_planta = ui.selecionar_entidade(db_path, "Selecione a Planta:", "plantas", ['id', 'codigo', 'numero_na_linha'], where)
    if not selecao_planta: return {'alvo_str': None}
    planta_id, codigo_planta, _ = selecao_planta
    
    return {'talhao_codigo': talhao_codigo, 'linha_id': linha_id, 'planta_id': planta_id, 'alvo_str': f'{nome_talhao} › Linha {numero_linha} › Planta {codigo_planta}'}

def registrar_atividade(db_path: str, contexto_pai: list):
    """Regista uma nova atividade agrícola no sistema."""
    contexto = contexto_pai + ["Registrar"]
    try:
        ui.limpar_tela(); ui.mostrar_logo("Registrar Atividade", contexto=contexto)
        selecao_tipo = ui.selecionar_entidade(db_path, "Selecione o tipo de atividade:", "tipos_atividades", ['id', 'nome'])
        if not selecao_tipo: return
        tipo_id, nome_tipo = selecao_tipo
        
        alvo = _selecionar_alvo(db_path)
        if not alvo or not alvo.get('alvo_str'): ui.mostrar_alerta("Registro cancelado."); return
        
        ui.limpar_tela(); ui.mostrar_logo(f"Registrar '{nome_tipo}'", contexto=contexto)
        print(f"\nAlvo Selecionado: {ui.Cores.VERDE}{alvo['alvo_str']}{ui.Cores.RESET}\n{'-'*60}")

        insumo_id, qtd, custo = None, None, None
        if input("Deseja associar um insumo? (s/n): ").lower() == 's':
            if executar_query(db_path, "SELECT COUNT(*) FROM insumos", fetch=True)[0][0] > 0:
                selecao_insumo = ui.selecionar_entidade(db_path, "Selecione o insumo:", "insumos", ['id', 'nome', 'unidade_medida'])
                if selecao_insumo:
                    insumo_id, nome_insumo, unidade = selecao_insumo
                    qtd = ui.obter_numero_positivo(f"Quantidade de '{nome_insumo}' ({unidade}): ")
                    custo = ui.obter_numero_positivo(f"Custo total (R$): ", permitir_vazio=True)
            else:
                ui.mostrar_erro("Nenhum insumo cadastrado.")
                if input("Continuar registo SEM insumo? (s/n): ").lower() != 's':
                    ui.mostrar_alerta("Registro cancelado."); return

        data_iso = ui.obter_data_valida("Data da execução")
        
        selecao_colab = ui.selecionar_entidade(db_path, "Selecione o Colaborador:", "colaboradores", ['id', 'nome_completo'], ("status = 'ativo'", []))
        if not selecao_colab: ui.mostrar_erro("A seleção de um colaborador é obrigatória."); return
        colaborador_id, _ = selecao_colab
        
        obs = input("Observações (opcional): ").strip() or None
        det = input("Detalhes técnicos (opcional): ").strip() or None

        query = "INSERT INTO registros_atividades (tipo_id, talhao_codigo, linha_id, planta_id, data, observacoes, detalhes, insumo_id, quantidade_insumo, custo_total, colaborador_id) VALUES (?,?,?,?,?,?,?,?,?,?,?)"
        params = (tipo_id, alvo.get('talhao_codigo'), alvo.get('linha_id'), alvo.get('planta_id'), data_iso, obs, det, insumo_id, qtd, custo, colaborador_id)
        
        if executar_query(db_path, query, params): ui.mostrar_sucesso("Atividade registrada!")
        else: ui.mostrar_erro("Erro ao registrar atividade")
    except Exception as e:
        logging.error(f"Erro ao registrar atividade: {e}", exc_info=True)
        ui.mostrar_erro(f"Erro: {e}")

def listar_atividades(db_path: str, contexto_pai: list):
    """Exibe uma lista paginada e filtrável de atividades registadas."""
    contexto = contexto_pai + ["Listagem"]
    try:
        while True:
            ui.limpar_tela(); ui.mostrar_logo("Filtrar Atividades", contexto=contexto)
            filtro_talhao, filtro_tipo = None, None
            
            if ui.selecionar_opcao_de_lista("Deseja filtrar?", ["Sim", "Não"], False) == "Sim":
                if ui.selecionar_opcao_de_lista("Filtrar por qual campo?", ["Talhão", "Tipo de Atividade"], False) == "Talhão":
                    selecao = ui.selecionar_entidade(db_path,"Selecione o Talhão:", "talhoes", ['codigo', 'nome'])
                    if selecao: filtro_talhao = selecao[0]
                else:
                    selecao = ui.selecionar_entidade(db_path, "Selecione o Tipo:", "tipos_atividades", ['id', 'nome'])
                    if selecao: filtro_tipo = selecao[0]

            ui.navegacao_paginada(
                db_path, contexto, "Atividades Registradas", "registros_atividades r",
                ["ID", "Data", "Tipo", "Colaborador", "Talhão", "Insumo", "Custo"],
                [4, 12, 18, 18, 10, 15, 12],
                ['r.id', 'r.data', 't.nome', 'c.nome_completo', 'r.talhao_codigo', 'i.nome', 'r.custo_total'],
                join_clause="""
                JOIN tipos_atividades t ON r.tipo_id = t.id
                LEFT JOIN colaboradores c ON r.colaborador_id = c.id
                LEFT JOIN insumos i ON r.insumo_id = i.id
                """,
                where_clause= ("r.talhao_codigo = ?" if filtro_talhao else "r.tipo_id = ?", [filtro_talhao or filtro_tipo]) if filtro_talhao or filtro_tipo else None,
                group_by_clause="r.id"
            )
            
            if ui.selecionar_opcao_de_lista("O que deseja fazer?", ["Filtrar Novamente", "Sair"], False) == "Sair":
                break
    except Exception as e:
        logging.error(f"Erro ao listar atividades: {e}", exc_info=True); ui.mostrar_erro(f"Erro: {e}")

def excluir_atividade_registrada(db_path: str, contexto_pai: list):
    """Permite que um administrador exclua um registo de atividade."""
    contexto = contexto_pai + ["Excluir"]
    try:
        ui.limpar_tela()
        ui.mostrar_logo("Excluir Atividade Registrada", contexto=contexto)
        
        selecao = ui.selecionar_entidade(db_path, "Selecione a atividade a excluir (pela data):", "registros_atividades", ['id', 'data'])
        if not selecao: return
        atividade_id, _ = selecao
        
        if input(f"\nTem certeza que deseja excluir o registro ID {atividade_id}? (s/n): ").lower() == 's':
            if executar_query(db_path, "DELETE FROM registros_atividades WHERE id = ?", (atividade_id,)):
                ui.mostrar_sucesso("Atividade excluída!")
            else: ui.mostrar_erro("Erro ao excluir.")
        else: ui.mostrar_alerta("Exclusão cancelada.")
    except Exception as e:
        logging.error(f"Erro ao excluir atividade: {e}", exc_info=True); ui.mostrar_erro(f"Erro: {e}")

def menu_tipos_atividades(db_path: str, usuario: dict, contexto_pai: list):
    """Menu para CRUD de Tipos de Atividades."""
    contexto = contexto_pai + ["Tipos de Atividade"]
    while True:
        ui.limpar_tela(); ui.mostrar_logo("Gerenciar Tipos de Atividades", contexto=contexto)
        print("\n[1] Cadastrar"); print("[2] Listar")
        if usuario["perfil"] == "admin": print("[3] Editar"); print("[4] Excluir")
        print("[0] Voltar")
        opcao = input("\n>>> ").strip()
        if opcao == "1": cadastrar_tipo_atividade(db_path, contexto)
        elif opcao == "2": listar_tipos_atividades(db_path, contexto)
        elif opcao == "3" and usuario["perfil"] == "admin": editar_tipo_atividade(db_path, contexto)
        elif opcao == "4" and usuario["perfil"] == "admin": excluir_tipo_atividade(db_path)
        elif opcao == "0": return
        else: ui.mostrar_erro("Opção inválida!")

def cadastrar_tipo_atividade(db_path: str, contexto_pai: list):
    """Regista um novo tipo de atividade (ex: Adubação, Pulverização)."""
    contexto = contexto_pai + ["Novo"]
    try:
        ui.limpar_tela(); ui.mostrar_logo("Cadastrar Tipo de Atividade", contexto=contexto)
        nome = input("Nome da atividade: ").strip()
        if not nome: ui.mostrar_erro("O nome é obrigatório."); return
        descricao = input("Descrição (opcional): ").strip()
        categoria = input("Categoria (ex: Nutrição, Fitossanitário): ").strip()
        recorrente = True if ui.selecionar_opcao_de_lista("É uma atividade recorrente?", ["Sim", "Não"], False) == "Sim" else False
        intervalo = None
        if recorrente:
            intervalo = ui.obter_numero_positivo("Intervalo de reaplicação (dias, opcional): ", tipo_dado=int, permitir_vazio=True)
        query = "INSERT INTO tipos_atividades (nome, descricao, categoria, recorrente, intervalo_dias) VALUES (?, ?, ?, ?, ?)"
        if executar_query(db_path, query, (nome, descricao, categoria, recorrente, intervalo)):
            ui.mostrar_sucesso("Tipo de atividade cadastrado!")
        else: ui.mostrar_erro("Erro ao cadastrar. O nome já pode existir.")
    except Exception as e: ui.mostrar_erro(f"Erro: {e}")

def listar_tipos_atividades(db_path: str, contexto_pai: list):
    """Exibe uma lista paginada de todos os tipos de atividades."""
    contexto = contexto_pai + ["Listagem"]
    ui.navegacao_paginada(db_path, contexto, "Tipos de Atividades", "tipos_atividades",
                         ["ID", "Nome", "Categoria", "Recorrente", "Intervalo (dias)"],
                         [4, 25, 20, 12, 18],
                         ['id', 'nome', 'categoria', "CASE WHEN recorrente THEN 'Sim' ELSE 'Não' END", 'intervalo_dias'])

def editar_tipo_atividade(db_path: str, contexto_pai: list):
    """Modifica um tipo de atividade existente."""
    contexto = contexto_pai + ["Editar"]
    try:
        selecao = ui.selecionar_entidade(db_path, "Selecione o tipo a editar:", "tipos_atividades", ['id', 'nome'])
        if not selecao: return
        tipo_id, nome_atual = selecao
        dados = executar_query(db_path, "SELECT * FROM tipos_atividades WHERE id=?",(tipo_id,), fetch=True)[0]
        ui.limpar_tela(); ui.mostrar_logo(f"Editando '{nome_atual}'", contexto=contexto)
        novo_nome = input(f"Nome [{dados[1]}]: ").strip() or dados[1]
        nova_desc = input(f"Descrição [{dados[2] or ''}]: ").strip() or dados[2]
        nova_cat = input(f"Categoria [{dados[3] or ''}]: ").strip() or dados[3]
        rec_atual_str = 'Sim' if dados[4] else 'Não'
        rec_str = ui.selecionar_opcao_de_lista(f"Recorrente? (Atual: {rec_atual_str})", ["Sim", "Não"], False)
        novo_rec = 1 if rec_str == 'Sim' else 0
        novo_intervalo = dados[5]
        if novo_rec:
            novo_intervalo = ui.obter_numero_positivo(f"Intervalo (dias) [{dados[5] or 'N/D'}]: ", tipo_dado=int, permitir_vazio=True) or dados[5]
        else:
            novo_intervalo = None
        query = "UPDATE tipos_atividades SET nome=?, descricao=?, categoria=?, recorrente=?, intervalo_dias=? WHERE id=?"
        params = (novo_nome, nova_desc, nova_cat, novo_rec, novo_intervalo, tipo_id)
        if executar_query(db_path, query, params): ui.mostrar_sucesso("Tipo atualizado!")
        else: ui.mostrar_erro("Falha ao atualizar.")
    except Exception as e: ui.mostrar_erro(f"Erro: {e}")

def excluir_tipo_atividade(db_path: str):
    """Remove um tipo de atividade, se não estiver em uso."""
    try:
        selecao = ui.selecionar_entidade(db_path, "Selecione o tipo a excluir:", "tipos_atividades", ['id', 'nome'])
        if not selecao: return
        tipo_id, nome_tipo = selecao
        registros = executar_query(db_path, "SELECT COUNT(*) FROM registros_atividades WHERE tipo_id=?",(tipo_id,), fetch=True)[0][0]
        if registros > 0:
            ui.mostrar_erro(f"'{nome_tipo}' não pode ser excluído (possui {registros} registros)."); return
        if input(f"Confirmar exclusão de '{nome_tipo}'? (s/n): ").lower() == 's':
            if executar_query(db_path, "DELETE FROM tipos_atividades WHERE id=?", (tipo_id,)):
                ui.mostrar_sucesso("Tipo de atividade excluído!")
            else: ui.mostrar_erro("Falha ao excluir.")
        else: ui.mostrar_alerta("Exclusão cancelada.")
    except Exception as e: ui.mostrar_erro(f"Erro: {str(e)}")

