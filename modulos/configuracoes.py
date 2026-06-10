# -*- coding: utf-8 -*-

"""
Venus Café - Módulo de Configurações do Sistema
===============================================

Este módulo permite que administradores configurem parâmetros globais do sistema,
como chaves de API para serviços externos.
"""

import logging
from modulos import ui
from database import executar_query

def _obter_config(db_path: str, chave: str) -> str | None:
    """Função auxiliar para ler uma configuração específica do banco de dados."""
    resultado = executar_query(db_path, "SELECT valor FROM configuracoes WHERE chave = ?", (chave,), fetch=True)
    return resultado[0][0] if resultado else None

def _salvar_config(db_path: str, chave: str, valor: str) -> bool:
    """Função auxiliar para salvar (inserir ou substituir) uma configuração."""
    query = "INSERT OR REPLACE INTO configuracoes (chave, valor) VALUES (?, ?)"
    return executar_query(db_path, query, (chave, valor))

def gerir_chaves_api(db_path: str, contexto_pai: list):
    """
    Apresenta uma interface para o administrador visualizar e atualizar
    as chaves de API para serviços externos.
    """
    contexto = contexto_pai + ["Chaves de API"]
    try:
        while True:
            ui.limpar_tela()
            ui.mostrar_logo("Gestão de Chaves de API", contexto=contexto)

            # Busca as chaves atuais no banco de dados
            chave_cotacao = _obter_config(db_path, 'API_KEY_COTACAO')
            chave_cambio = _obter_config(db_path, 'API_KEY_CAMBIO')

            # Mostra as chaves de forma segura (mascarada)
            chave_cotacao_display = f"***{chave_cotacao[-4:]}" if chave_cotacao else "Não definida"
            chave_cambio_display = f"***{chave_cambio[-4:]}" if chave_cambio else "Não definida"

            print(f"\n1. Chave API Cotações (Alpha Vantage): {chave_cotacao_display}")
            print(f"2. Chave API Câmbio (ex: ExchangeRate-API): {chave_cambio_display}")
            print("\n[0] Voltar")

            opcao = ui.selecionar_opcao_de_lista(
                "\nQual chave de API deseja editar?",
                ["API de Cotações", "API de Câmbio"],
                pode_cancelar=True
            )

            if not opcao:
                return

            if opcao == "API de Cotações":
                chave = 'API_KEY_COTACAO'
                prompt = "Insira a sua nova chave da Alpha Vantage: "
            else: # API de Câmbio
                chave = 'API_KEY_CAMBIO'
                prompt = "Insira a sua nova chave da API de Câmbio: "

            novo_valor = input(f"\n{prompt}").strip()
            if novo_valor:
                if _salvar_config(db_path, chave, novo_valor):
                    ui.mostrar_sucesso("Chave de API salva com sucesso!")
                else:
                    ui.mostrar_erro("Falha ao salvar a chave de API.")
            else:
                ui.mostrar_alerta("Nenhuma alteração feita.")
    
    except Exception as e:
        logging.error(f"Erro ao gerir chaves de API: {e}", exc_info=True)
        ui.mostrar_erro(f"Ocorreu um erro inesperado: {e}")

def menu_configuracoes(usuario: dict, db_path: str, contexto_pai: list):
    """Menu principal para o módulo de Configurações."""
    contexto = contexto_pai + ["Configurações"]
    while True:
        ui.limpar_tela()
        ui.mostrar_logo("Configurações do Sistema", contexto=contexto)
        
        print("\n[1] Gerir Chaves de API")
        print("[0] Voltar")
        
        opcao = input("\n>>> Selecione: ").strip()
        if opcao == '1':
            gerir_chaves_api(db_path, contexto)
        elif opcao == '0':
            return
        else:
            ui.mostrar_erro("Opção inválida.")
