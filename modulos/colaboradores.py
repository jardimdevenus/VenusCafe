# -*- coding: utf-8 -*-

"""
Venus Café - Módulo de Gestão de Colaboradores
==============================================

Este módulo centraliza as funcionalidades para gerir os colaboradores de campo,
que são as pessoas que executam as atividades agrícolas.
"""

import sqlite3
import logging
from modulos import ui
from database import executar_query

def menu_colaboradores(db_path: str, usuario: dict):
    """
    Exibe o menu principal para a gestão de colaboradores de campo.

    Args:
        db_path (str): Caminho para o arquivo do banco de dados.
        usuario (dict): Dicionário do utilizador logado para verificação de permissões.
    """
    contexto = ["Gestão de Pessoas", "Colaboradores"]
    while True:
        ui.limpar_tela()
        ui.mostrar_logo("Gestão de Colaboradores de Campo", contexto=contexto)
        
        print("\n[1] Cadastrar Novo Colaborador")
        print("[2] Listar Colaboradores")
        if usuario["perfil"] == "admin":
            print("[3] Editar Colaborador")
            print("[4] Excluir Colaborador")
        print("[0] Voltar")
        
        opcao = input("\n>>> Selecione: ").strip()
        
        if opcao == "1":
            cadastrar_colaborador(db_path)
        elif opcao == "2":
            listar_colaboradores(db_path)
        elif opcao == "3" and usuario["perfil"] == "admin":
            editar_colaborador(db_path)
        elif opcao == "4" and usuario["perfil"] == "admin":
            excluir_colaborador(db_path)
        elif opcao == "0":
            return
        else:
            ui.mostrar_erro("Opção inválida!")

def cadastrar_colaborador(db_path: str):
    """Regista um novo colaborador no sistema."""
    contexto = ["Gestão de Pessoas", "Colaboradores", "Novo"]
    try:
        ui.limpar_tela()
        ui.mostrar_logo("Cadastrar Novo Colaborador", contexto=contexto)
        
        nome = input("Nome completo do colaborador: ").strip()
        if not nome:
            ui.mostrar_erro("O nome é obrigatório!"); return

        funcao = input("Função/Cargo (ex: Colhedor, Tratorista): ").strip() or "Não especificada"
            
        query = "INSERT INTO colaboradores (nome_completo, funcao, status) VALUES (?, ?, 'ativo')"
        params = (nome, funcao)
        
        if executar_query(db_path, query, params):
            ui.mostrar_sucesso(f"Colaborador '{nome}' cadastrado com sucesso!")
        else:
            ui.mostrar_erro("Erro ao cadastrar. O nome já pode existir.")
            
    except sqlite3.IntegrityError:
        ui.mostrar_erro(f"O colaborador '{nome}' já existe no banco de dados.")
    except Exception as e:
        logging.error(f"Erro ao cadastrar colaborador: {e}", exc_info=True)
        ui.mostrar_erro(f"Ocorreu um erro: {e}")

def listar_colaboradores(db_path: str):
    """
    Apresenta um menu para filtrar colaboradores por status e exibe o resultado
    numa lista paginada e ordenada por nome.
    """
    contexto = ["Gestão de Pessoas", "Colaboradores"]
    
    while True:
        ui.limpar_tela()
        ui.mostrar_logo("Listar Colaboradores", contexto=contexto)
        
        filtro_escolhido = ui.selecionar_opcao_de_lista(
            "Filtrar por status:",
            ["Ativos", "Inativos", "Todos"]
        )
        if not filtro_escolhido: return

        where_clause = None
        if filtro_escolhido == 'Ativos':
            where_clause = ("status = ?", ["ativo"])
        elif filtro_escolhido == 'Inativos':
            where_clause = ("status = ?", ["inativo"])

        titulo = f"Colaboradores ({filtro_escolhido})"
        nome_tabela = "colaboradores"
        cabecalhos = ["ID", "Nome Completo", "Função", "Status"]
        larguras = [4, 35, 25, 10]
        colunas_db = ['id', 'nome_completo', 'funcao', 'status']
        
        ui.navegacao_paginada(
            db_path, contexto, titulo, nome_tabela, cabecalhos, larguras, colunas_db,
            where_clause=where_clause,
            order_by_clause="nome_completo ASC" # <-- GARANTE A ORDEM ALFABÉTICA
        )
        
        if ui.selecionar_opcao_de_lista("\nO que deseja fazer?", ["Fazer outra consulta", "Sair"], False) == "Sair":
            break

def editar_colaborador(db_path: str):
    """Modifica os dados de um colaborador existente, incluindo o seu status."""
    contexto = ["Gestão de Pessoas", "Colaboradores", "Editar"]
    try:
        selecao = ui.selecionar_entidade(db_path, "Selecione o colaborador a editar:",
                                         "colaboradores", ['id', 'nome_completo'])
        if not selecao: return
        colab_id, nome_colab = selecao

        dados_atuais = executar_query(db_path, "SELECT nome_completo, funcao, status FROM colaboradores WHERE id = ?", (colab_id,), fetch=True)[0]

        ui.limpar_tela()
        ui.mostrar_logo(f"Editando: {nome_colab}", contexto=contexto)
        print("\nDeixe em branco para manter o valor atual.")

        novo_nome = input(f"Nome [{dados_atuais[0]}]: ").strip() or dados_atuais[0]
        nova_funcao = input(f"Função [{dados_atuais[1]}]: ").strip() or dados_atuais[1]
        
        novo_status = ui.selecionar_opcao_de_lista(
            f"Status atual: {dados_atuais[2]}. Selecione o novo status:",
            ["ativo", "inativo"], pode_cancelar=True
        ) or dados_atuais[2]

        query = "UPDATE colaboradores SET nome_completo = ?, funcao = ?, status = ? WHERE id = ?"
        params = (novo_nome, nova_funcao, novo_status, colab_id)

        if executar_query(db_path, query, params):
            ui.mostrar_sucesso("Colaborador atualizado!")
        else:
            ui.mostrar_erro("Erro ao atualizar. O nome já pode existir.")
    except sqlite3.IntegrityError:
        ui.mostrar_erro(f"O nome '{novo_nome}' já está em uso.")
    except Exception as e:
        logging.error(f"Erro ao editar colaborador: {e}", exc_info=True)
        ui.mostrar_erro(f"Ocorreu um erro: {e}")

def excluir_colaborador(db_path: str):
    """
    Remove um colaborador do sistema, apenas se não tiver histórico de atividades.
    """
    contexto = ["Gestão de Pessoas", "Colaboradores", "Excluir"]
    try:
        ui.limpar_tela()
        ui.mostrar_logo("Excluir Colaborador", contexto=contexto)
        
        selecao = ui.selecionar_entidade(db_path, "Selecione o colaborador a excluir:",
                                         "colaboradores", ['id', 'nome_completo'])
        if not selecao: return
        colab_id, nome_colab = selecao

        # Verificação de dependência no histórico de atividades
        query_check = "SELECT COUNT(*) FROM registros_atividades WHERE colaborador_id = ?"
        registros = executar_query(db_path, query_check, (colab_id,), fetch=True)
        if registros and registros[0][0] > 0:
            ui.mostrar_erro(f"'{nome_colab}' não pode ser excluído.")
            ui.mostrar_alerta(f"Este colaborador está associado a {registros[0][0]} atividades no histórico.")
            ui.mostrar_alerta("Considere alterar o status para 'inativo' em vez de excluir.")
            input("Pressione Enter para continuar..."); return

        confirmacao = input(f"Digite 'CONFIRMAR' para excluir permanentemente '{nome_colab}': ").strip()
        if confirmacao == "CONFIRMAR":
            if executar_query(db_path, "DELETE FROM colaboradores WHERE id = ?", (colab_id,)):
                ui.mostrar_sucesso("Colaborador excluído com sucesso!")
            else: ui.mostrar_erro("Falha ao excluir o colaborador.")
        else:
            ui.mostrar_alerta("Exclusão cancelada.")
    except Exception as e:
        logging.error(f"Erro ao excluir colaborador: {e}", exc_info=True)
        ui.mostrar_erro(f"Ocorreu um erro: {e}")
