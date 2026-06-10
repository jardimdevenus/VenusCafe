# -*- coding: utf-8 -*-

"""
Venus Café - Módulo de Gestão de Insumos
========================================

Este módulo é responsável pelo CRUD (Create, Read, Update, Delete)
de insumos, como fertilizantes, defensivos, etc., utilizados nas
atividades agrícolas.
"""

import sqlite3
import logging
from modulos import ui
from database import executar_query

def menu_insumos(usuario: dict, db_path: str):
    """
    Exibe o menu principal para a gestão de insumos.

    Args:
        usuario (dict): Dicionário do utilizador logado.
        db_path (str): Caminho para o arquivo do banco de dados.
    """
    contexto = ["Gestão de Insumos"]
    while True:
        ui.limpar_tela()
        ui.mostrar_logo("Gestão de Insumos", contexto=contexto)
        
        print("\n[1] Cadastrar Novo Insumo")
        print("[2] Listar Insumos Cadastrados")
        if usuario["perfil"] == "admin":
            print("[3] Editar Insumo")
            print("[4] Excluir Insumo")
        print("[0] Voltar")
        
        opcao = input("\n>>> Selecione: ").strip()
        
        if opcao == "1":
            cadastrar_insumo(db_path)
        elif opcao == "2":
            listar_insumos(db_path)
        elif opcao == "3" and usuario["perfil"] == "admin":
            editar_insumo(db_path)
        elif opcao == "4" and usuario["perfil"] == "admin":
            excluir_insumo(db_path)
        elif opcao == "0":
            return
        else:
            ui.mostrar_erro("Opção inválida!")

def cadastrar_insumo(db_path: str):
    """Regista um novo insumo no sistema."""
    contexto = ["Gestão de Insumos", "Novo"]
    try:
        ui.limpar_tela()
        ui.mostrar_logo("Cadastrar Novo Insumo", contexto=contexto)
        
        nome = input("Nome do insumo (ex: Ureia): ").strip()
        if not nome:
            ui.mostrar_erro("O nome é obrigatório!"); return

        categoria = input("Categoria (ex: Fertilizante, Fungicida): ").strip()
        unidade = input("Unidade de medida padrão (ex: kg, L, Ton): ").strip()
        if not unidade:
            ui.mostrar_erro("A unidade de medida é obrigatória!"); return
            
        query = "INSERT INTO insumos (nome, categoria, unidade_medida) VALUES (?, ?, ?)"
        params = (nome, categoria, unidade)
        
        if executar_query(db_path, query, params):
            ui.mostrar_sucesso("Insumo cadastrado com sucesso!")
        else:
            ui.mostrar_erro("Erro ao cadastrar. O nome já pode existir.")
    except sqlite3.IntegrityError:
        ui.mostrar_erro(f"O insumo '{nome}' já existe.")
    except Exception as e:
        logging.error(f"Erro ao cadastrar insumo: {e}", exc_info=True)
        ui.mostrar_erro(f"Ocorreu um erro: {e}")

def listar_insumos(db_path: str):
    """
    Exibe uma lista paginada de todos os insumos registados, ordenada
    alfabeticamente por nome.
    """
    contexto = ["Gestão de Insumos", "Listagem"]
    titulo = "Insumos Cadastrados"
    nome_tabela = "insumos"
    cabecalhos = ["ID", "Nome do Insumo", "Categoria", "Unidade"]
    larguras = [4, 30, 25, 10]
    colunas_db = ['id', 'nome', 'categoria', 'unidade_medida']
    
    ui.navegacao_paginada(
        db_path, contexto, titulo, nome_tabela, cabecalhos, larguras, colunas_db,
        order_by_clause="nome ASC"
    )


def editar_insumo(db_path: str):
    """Modifica os dados de um insumo existente."""
    contexto = ["Gestão de Insumos", "Editar"]
    try:
        selecao = ui.selecionar_entidade(db_path, "Selecione o insumo a editar:",
                                         "insumos", ['id', 'nome'])
        if not selecao: return
        insumo_id, nome_atual = selecao

        dados_atuais = executar_query(db_path, "SELECT nome, categoria, unidade_medida FROM insumos WHERE id = ?", (insumo_id,), fetch=True)[0]

        ui.limpar_tela()
        ui.mostrar_logo(f"Editando Insumo: {nome_atual}", contexto=contexto)
        print("\nDeixe em branco para manter o valor atual.")

        novo_nome = input(f"Nome [{dados_atuais[0]}]: ").strip() or dados_atuais[0]
        nova_cat = input(f"Categoria [{dados_atuais[1]}]: ").strip() or dados_atuais[1]
        nova_un = input(f"Unidade [{dados_atuais[2]}]: ").strip() or dados_atuais[2]

        query = "UPDATE insumos SET nome = ?, categoria = ?, unidade_medida = ? WHERE id = ?"
        params = (novo_nome, nova_cat, nova_un, insumo_id)

        if executar_query(db_path, query, params):
            ui.mostrar_sucesso("Insumo atualizado com sucesso!")
        else:
            ui.mostrar_erro("Erro ao atualizar. O nome já pode existir.")
    except sqlite3.IntegrityError:
        ui.mostrar_erro(f"O nome de insumo '{novo_nome}' já está em uso.")
    except Exception as e:
        logging.error(f"Erro ao editar insumo: {e}", exc_info=True)
        ui.mostrar_erro(f"Ocorreu um erro: {e}")

def excluir_insumo(db_path: str):
    """Remove um insumo, apenas se não estiver associado a nenhuma atividade."""
    contexto = ["Gestão de Insumos", "Excluir"]
    try:
        ui.limpar_tela()
        ui.mostrar_logo("Excluir Insumo", contexto=contexto)
        
        selecao = ui.selecionar_entidade(db_path, "Selecione o insumo a excluir:",
                                         "insumos", ['id', 'nome'])
        if not selecao: return
        insumo_id, nome_insumo = selecao

        query_check = "SELECT COUNT(*) FROM registros_atividades WHERE insumo_id = ?"
        registros = executar_query(db_path, query_check, (insumo_id,), fetch=True)
        if registros and registros[0][0] > 0:
            ui.mostrar_erro(f"'{nome_insumo}' não pode ser excluído.")
            ui.mostrar_alerta(f"Está associado a {registros[0][0]} atividade(s) no histórico.")
            input("Pressione Enter para continuar..."); return

        confirmacao = input(f"Digite 'CONFIRMAR' para excluir '{nome_insumo}': ").strip()
        if confirmacao == "CONFIRMAR":
            if executar_query(db_path, "DELETE FROM insumos WHERE id = ?", (insumo_id,)):
                ui.mostrar_sucesso("Insumo excluído com sucesso!")
            else: ui.mostrar_erro("Falha ao excluir o insumo.")
        else:
            ui.mostrar_alerta("Exclusão cancelada.")
    except Exception as e:
        logging.error(f"Erro ao excluir insumo: {e}", exc_info=True)
        ui.mostrar_erro(f"Ocorreu um erro: {e}")
