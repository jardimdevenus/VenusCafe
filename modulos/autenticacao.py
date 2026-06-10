# -*- coding: utf-8 -*-

"""
Venus Café - Módulo de Autenticação e Gestão de Utilizadores
============================================================

Este módulo gere todas as operações relacionadas com os utilizadores do sistema,
incluindo o processo de login, registo, listagem, edição e exclusão de contas.
"""

import os
import hashlib
import sqlite3
import logging
import time
from modulos import ui
from database import executar_query

def fazer_login(db_path: str) -> dict | None:
    """
    Autentica um utilizador no sistema.

    Apresenta uma tela de login, captura o utilizador e a senha (mascarada),
    e verifica as credenciais contra os dados 'hasheados' no banco de dados.
    Permite um máximo de 3 tentativas.

    Args:
        db_path (str): Caminho para o arquivo do banco de dados.

    Returns:
        dict | None: Um dicionário com os dados do utilizador se o login for
                     bem-sucedido, ou None em caso de falha.
    """
    tentativas = 0
    max_tentativas = 3
    while tentativas < max_tentativas:
        try:
            ui.mostrar_tela_login()
            print(f"{ui.Cores.AMARELO}Por favor, faça o login para continuar.{ui.Cores.RESET}")
            
            usuario = input("Usuário: ")
            senha = ui.obter_senha_mascarada("Senha:   ")
            
            query = "SELECT id, hash_senha, sal, nome_completo, perfil FROM usuarios WHERE usuario = ?"
            resultado = executar_query(db_path, query, (usuario,), fetch=True)
            
            if not resultado or not resultado[0]:
                raise ValueError("Utilizador ou senha inválidos.")
            
            dados_db = resultado[0]
            id_user, hash_db, sal_hex, nome, perfil = dados_db
            sal = bytes.fromhex(sal_hex)
            
            hash_fornecida = hashlib.pbkdf2_hmac('sha256', senha.encode(), sal, 100000).hex()
            
            if hash_fornecida != hash_db:
                raise ValueError("Utilizador ou senha inválidos.")
            
            print(f"\n{ui.Cores.VERDE}Autenticação bem-sucedida. A carregar sistema...{ui.Cores.RESET}")
            time.sleep(1)
                
            return {"id": id_user, "usuario": usuario, "nome": nome, "perfil": perfil}

        except ValueError as e:
            tentativas += 1
            ui.mostrar_erro(f"{e} (Tentativa {tentativas}/{max_tentativas})")
        except Exception as e:
            tentativas += 1
            logging.error(f"Erro inesperado durante o login: {e}", exc_info=True)
            ui.mostrar_erro(f"Ocorreu um erro. (Tentativa {tentativas}/{max_tentativas})")
    
    ui.mostrar_erro("Número máximo de tentativas excedido.")
    return None

def menu_administracao_usuarios(db_path: str, usuario: dict):
    """
    Exibe o menu de gestão de utilizadores (disponível para administradores).
    """
    contexto = ["Gestão de Pessoas", "Usuários do Sistema"]
    while True:
        ui.limpar_tela()
        ui.mostrar_logo("Administração de Usuários", contexto=contexto)
        
        print("\n[1] Cadastrar Novo Usuário")
        print("[2] Listar Usuários")
        print("[3] Editar Usuário")
        print("[4] Excluir Usuário")
        print("[0] Voltar")
        
        opcao = input("\n>>> Selecione: ").strip()
        
        if opcao == "1": cadastrar_usuario(db_path)
        elif opcao == "2": listar_usuarios(db_path)
        elif opcao == "3": editar_usuario(db_path)
        elif opcao == "4": excluir_usuario(db_path)
        elif opcao == "0": break
        else: ui.mostrar_erro("Opção inválida!")

def cadastrar_usuario(db_path: str) -> bool:
    """Regista um novo utilizador no banco de dados."""
    contexto = ["Gestão de Pessoas", "Usuários", "Novo"]
    try:
        ui.limpar_tela()
        ui.mostrar_logo("Cadastrar Novo Usuário", contexto=contexto)
        
        usuario = input("Nome de usuário: ").strip()
        if not usuario: ui.mostrar_erro("Nome de usuário não pode ser vazio."); return False

        senha = ui.obter_senha_mascarada("Senha: ")
        confirmar_senha = ui.obter_senha_mascarada("Confirmar senha: ")
        
        if not senha: ui.mostrar_erro("A senha não pode estar em branco!"); return False
        if senha != confirmar_senha: ui.mostrar_erro("As senhas não coincidem!"); return False
        
        sal = os.urandom(16)
        hash_senha = hashlib.pbkdf2_hmac('sha256', senha.encode(), sal, 100000).hex()
        
        nome_completo = input("Nome completo: ").strip()
        email = input("Email (opcional): ").strip()
        perfil = input("Perfil (admin/user) [user]: ").strip().lower() or 'user'
        if perfil not in ['admin', 'user']: perfil = 'user'
        
        query = "INSERT INTO usuarios (usuario, hash_senha, sal, nome_completo, email, perfil) VALUES (?, ?, ?, ?, ?, ?)"
        params = (usuario, hash_senha, sal.hex(), nome_completo, email, perfil)
        
        if executar_query(db_path, query, params):
            ui.mostrar_sucesso("Usuário cadastrado com sucesso!"); return True
        return False
    except sqlite3.IntegrityError:
        ui.mostrar_erro(f"O nome de usuário '{usuario}' já existe!"); return False
    except Exception as e:
        logging.error(f"Erro ao cadastrar usuário: {e}", exc_info=True)
        ui.mostrar_erro(f"Erro ao cadastrar: {e}"); return False

def listar_usuarios(db_path: str):
    """
    Exibe uma lista paginada de todos os utilizadores registados, ordenada
    alfabeticamente por nome completo.
    """
    contexto = ["Gestão de Pessoas", "Usuários"]
    titulo = "Usuários do Sistema Cadastrados"
    nome_tabela = "usuarios"
    cabecalhos = ["ID", "Usuário", "Nome Completo", "Perfil", "Email"]
    larguras = [4, 15, 25, 10, 25]
    colunas_db = ['id', 'usuario', 'nome_completo', 'perfil', 'email']
    
    ui.navegacao_paginada(
        db_path, contexto, titulo, nome_tabela, cabecalhos, larguras, colunas_db,
        order_by_clause="nome_completo ASC" 
    )


def editar_usuario(db_path: str):
    """Modifica os dados de um utilizador existente."""
    contexto = ["Gestão de Pessoas", "Usuários", "Editar"]
    try:
        ui.limpar_tela()
        ui.mostrar_logo("Editar Usuário", contexto=contexto)
        
        id_str = input("ID do usuário a editar (deixe em branco para cancelar): ").strip()
        if not id_str: return
        
        usuario_id = int(id_str)
        dados = executar_query(db_path, "SELECT * FROM usuarios WHERE id = ?", (usuario_id,), fetch=True)
        if not dados: ui.mostrar_erro("Usuário não encontrado!"); return
        
        user_atual = dados[0]
        
        contexto_edit = contexto + [f"{user_atual[1]}"]
        ui.limpar_tela()
        ui.mostrar_logo(f"Editando: {user_atual[1]}", contexto=contexto_edit)
        print("Deixe em branco para manter o valor atual.\n")
        
        novo_usuario = input(f"Usuário [{user_atual[1]}]: ").strip() or user_atual[1]
        novo_nome = input(f"Nome completo [{user_atual[4]}]: ").strip() or user_atual[4]
        novo_email = input(f"Email [{user_atual[5] or ''}]: ").strip() or user_atual[5]
        novo_perfil = input(f"Perfil (admin/user) [{user_atual[6]}]: ").strip().lower() or user_atual[6]
        if novo_perfil not in ['admin', 'user']:
            ui.mostrar_erro("Perfil inválido! Mantendo o perfil atual."); novo_perfil = user_atual[6]
        
        if user_atual[6] == 'admin' and novo_perfil == 'user':
            count_admin = executar_query(db_path, "SELECT COUNT(*) FROM usuarios WHERE perfil = 'admin'", fetch=True)
            if count_admin and count_admin[0][0] <= 1:
                ui.mostrar_erro("Não é possível rebaixar o único administrador!"); return
        
        nova_senha = ui.obter_senha_mascarada("Nova senha (deixe em branco para não alterar): ")
        
        if nova_senha:
            sal = os.urandom(16)
            hash_senha = hashlib.pbkdf2_hmac('sha256', nova_senha.encode(), sal, 100000).hex()
            query = "UPDATE usuarios SET usuario=?, nome_completo=?, email=?, perfil=?, hash_senha=?, sal=? WHERE id=?"
            params = (novo_usuario, novo_nome, novo_email, novo_perfil, hash_senha, sal.hex(), usuario_id)
        else:
            query = "UPDATE usuarios SET usuario=?, nome_completo=?, email=?, perfil=? WHERE id=?"
            params = (novo_usuario, novo_nome, novo_email, novo_perfil, usuario_id)
        
        if executar_query(db_path, query, params): ui.mostrar_sucesso("Usuário atualizado!")
        else: ui.mostrar_erro("Erro ao atualizar. O nome de usuário já pode existir.")
            
    except ValueError: ui.mostrar_erro("ID inválido. Deve ser um número.")
    except sqlite3.IntegrityError: ui.mostrar_erro(f"O nome de usuário '{novo_usuario}' já está em uso.")
    except Exception as e:
        logging.error(f"Erro ao editar usuário: {e}", exc_info=True)
        ui.mostrar_erro(f"Erro ao editar usuário: {e}")

def excluir_usuario(db_path: str):
    """Remove um utilizador do sistema."""
    contexto = ["Gestão de Pessoas", "Usuários", "Excluir"]
    try:
        ui.limpar_tela()
        ui.mostrar_logo("Excluir Usuário", contexto=contexto)
        id_str = input("ID do usuário a excluir (deixe em branco para cancelar): ").strip()
        if not id_str: return
        
        usuario_id = int(id_str)
        dados = executar_query(db_path, "SELECT usuario, perfil FROM usuarios WHERE id = ?", (usuario_id,), fetch=True)
        if not dados: ui.mostrar_erro("Usuário não encontrado!"); return

        user_nome, user_perfil = dados[0]
        if user_perfil == 'admin':
            count_admin = executar_query(db_path, "SELECT COUNT(*) FROM usuarios WHERE perfil = 'admin'", fetch=True)
            if count_admin and count_admin[0][0] <= 1:
                ui.mostrar_erro("Não é possível excluir o único administrador do sistema!"); return

        confirmacao = input(f"Digite 'CONFIRMAR' para excluir o usuário '{user_nome}': ").strip()
        if confirmacao == "CONFIRMAR":
            if executar_query(db_path, "DELETE FROM usuarios WHERE id = ?", (usuario_id,)):
                ui.mostrar_sucesso("Usuário excluído com sucesso!")
            else: ui.mostrar_erro("Erro ao excluir usuário")
        else: ui.mostrar_alerta("Exclusão cancelada.")
    except ValueError: ui.mostrar_erro("ID inválido. Deve ser um número.")
    except Exception as e:
        logging.error(f"Erro ao excluir usuário: {e}", exc_info=True)
        ui.mostrar_erro(f"Erro ao excluir usuário: {e}")
