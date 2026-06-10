# -*- coding: utf-8 -*-

"""
Venus Café - Sistema de Gestão de Cafeicultura - Módulo Principal
"""
import os
import sys
import time
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s', stream=sys.stdout)

try:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    MODULOS_DIR = os.path.join(BASE_DIR, "modulos")
    DADOS_DIR = os.path.join(BASE_DIR, "dados")
    BACKUP_DIR = os.path.join(BASE_DIR, "backups")
    DATABASE_PATH = os.path.join(DADOS_DIR, "venus_cafe.db")
    if MODULOS_DIR not in sys.path:
        sys.path.insert(0, MODULOS_DIR)
except Exception as e:
    print(f"ERRO CRÍTICO ao configurar caminhos: {e}"); sys.exit(1)

try:
    from database import criar_banco_dados, fazer_backup
    from autenticacao import fazer_login, menu_administracao_usuarios
    from perfil import gerenciar_perfil_agricultor, visualizar_perfil, mostrar_resumo_propriedade
    from ui import mostrar_logo, limpar_tela, mostrar_erro, mostrar_alerta, mostrar_tela_sobre, mostrar_manual_usuario
    from cultivares import menu_cultivares
    from talhoes import menu_talhoes
    from insumos import menu_insumos
    from colaboradores import menu_colaboradores
    from atividades import menu_atividades
    from clima import menu_clima
    from analises import menu_analises
    from relatorios import menu_relatorios 
except ImportError as e:
    logging.critical(f"Erro ao importar módulos: {e}", exc_info=True)
    print("\nERRO CRÍTICO: Não foi possível carregar módulos essenciais."); sys.exit(1)

def inicializar_sistema() -> bool:
    """Prepara o ambiente da aplicação."""
    try:
        os.makedirs(DADOS_DIR, exist_ok=True)
        os.makedirs(BACKUP_DIR, exist_ok=True)
        if not criar_banco_dados(DATABASE_PATH):
            raise ConnectionError("Falha ao criar/verificar o banco de dados.")
        fazer_backup(DATABASE_PATH, BACKUP_DIR)
        return True
    except Exception as e:
        logging.critical(f"Falha na inicialização: {e}", exc_info=True)
        mostrar_erro(f"Falha na inicialização: {e}"); return False

def menu_principal(usuario: dict):
    """Exibe o menu principal reestruturado com sub-menus."""
    while True:
        limpar_tela()
        mostrar_logo(f"Bem-vindo, {usuario['nome']}")
        print("\n[1] Operações de Campo")
        print("[2] Cadastros de Base")
        print("[3] Ferramentas Avançadas")
        print("-----------------------------")
        print("[4] Perfil da Propriedade")
        if usuario["perfil"] == "admin":
            print("[5] Gestão de Pessoas")
            print("[6] Configurações")
            print("[7] Sobre o Venus Café")
            print("[8] Ajuda/Manual")
        print("[0] Sair do Sistema")
        
        try:
            opcao = input("\n>>> Selecione uma opção: ").strip()

            if opcao == "1":
                contexto_pai = ["Operações de Campo"]
                while True:
                    limpar_tela()
                    mostrar_logo("Operações de Campo", contexto=contexto_pai)
                    print("\n[1] Registrar Atividade Agrícola")
                    print("[2] Listar Atividades Registradas")
                    print("[0] Voltar")
                    sub_opcao = input("\n>>> ").strip()
                    if sub_opcao == '1': menu_atividades(usuario, DATABASE_PATH)
                    elif sub_opcao == '2': 
                        from atividades import listar_atividades
                        listar_atividades(DATABASE_PATH, contexto_pai)
                    elif sub_opcao == '0': break
                    else: mostrar_erro("Opção inválida.")
            
            elif opcao == "2":
                contexto_pai = ["Cadastros de Base"]
                while True:
                    limpar_tela()
                    mostrar_logo("Cadastros de Base", contexto=contexto_pai)
                    print("\n[1] Gestão de Talhões, Linhas e Plantas")
                    print("[2] Gestão de Cultivares")
                    print("[3] Gestão de Insumos")
                    print("[0] Voltar")
                    sub_opcao = input("\n>>> ").strip()
                    if sub_opcao == '1': menu_talhoes(usuario, DATABASE_PATH)
                    elif sub_opcao == '2': menu_cultivares(usuario, DATABASE_PATH)
                    elif sub_opcao == '3': menu_insumos(usuario, DATABASE_PATH)
                    elif sub_opcao == '0': break
                    else: mostrar_erro("Opção inválida.")

            elif opcao == "3":
                contexto_pai = ["Ferramentas Avançadas"]
                while True:
                    limpar_tela()
                    mostrar_logo("Ferramentas Avançadas", contexto=contexto_pai)
                    print("\n[1] Clima & Ambiente")
                    print("[2] Análises (Solo/Folha)")
                    print("[3] Relatórios & Análises")
                    print("[0] Voltar")
                    sub_opcao = input("\n>>> ").strip()
                    if sub_opcao == '1': menu_clima(usuario, DATABASE_PATH, contexto_pai)
                    elif sub_opcao == '2': menu_analises(usuario, DATABASE_PATH, contexto_pai)
                    elif sub_opcao == '3':
                        menu_relatorios(usuario, DATABASE_PATH, contexto_pai)
                    elif sub_opcao == '0': break
                    else: mostrar_erro("Opção inválida.")

            elif opcao == "4":
                while True:
                    limpar_tela(); mostrar_logo("Perfil da Propriedade", contexto=["Perfil"])
                    if usuario["perfil"] == "admin": print("\n[1] Editar Perfil")
                    print("[2] Visualizar Perfil"); print("[3] Resumo da Propriedade")
                    print("[0] Voltar")
                    sub_opcao = input("\n>>> ").strip()
                    if sub_opcao == "1" and usuario["perfil"] == "admin": gerenciar_perfil_agricultor(DATABASE_PATH)
                    elif sub_opcao == "2": visualizar_perfil(DATABASE_PATH)
                    elif sub_opcao == "3": mostrar_resumo_propriedade(DATABASE_PATH)
                    elif sub_opcao == '0': break
                    else: mostrar_erro("Opção inválida.")

            elif opcao == "5" and usuario["perfil"] == "admin":
                while True:
                    limpar_tela(); mostrar_logo("Gestão de Pessoas", contexto=["Pessoas"])
                    print("\n[1] Gerenciar Usuários"); print("[2] Gerenciar Colaboradores")
                    print("[0] Voltar")
                    sub_opcao = input("\n>>> ").strip()
                    if sub_opcao == "1": menu_administracao_usuarios(DATABASE_PATH, usuario)
                    elif sub_opcao == "2": menu_colaboradores(DATABASE_PATH, usuario)
                    elif sub_opcao == '0': break
                    else: mostrar_erro("Opção inválida.")
            
            elif opcao == "6" and usuario["perfil"] == "admin":
                from configuracoes import menu_configuracoes
                menu_configuracoes(usuario, DATABASE_PATH, ["Configurações"])
            elif opcao == "7":
                mostrar_tela_sobre()
            elif opcao == "8":
                mostrar_manual_usuario(contexto_pai="Menu Principal")
            elif opcao == "0":
                print("\nSaindo do sistema..."); time.sleep(1); sys.exit(0)
            else:
                mostrar_erro("Opção inválida!")
        except KeyboardInterrupt:
            print("\nSaindo..."); sys.exit(0)
        except Exception as e:
            logging.error(f"Erro no menu: {e}", exc_info=True); mostrar_erro(f"Erro: {e}")

if __name__ == "__main__":
    try:
        logging.info("Iniciando sistema Venus Café...")
        if not inicializar_sistema(): sys.exit(1)
        usuario_logado = fazer_login(DATABASE_PATH)
        if usuario_logado:
            menu_principal(usuario_logado)
        else:
            logging.warning("Falha no login."); print("\nEncerrando o sistema."); sys.exit(1)
    except Exception as e:
        logging.critical(f"Falha crítica no arranque: {e}", exc_info=True)
        try:
            mostrar_erro("Ocorreu um erro grave e o sistema foi encerrado.")
        except:
            print(f"ERRO GRAVE: {e}")
        sys.exit(1)
