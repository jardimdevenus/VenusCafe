# -*- coding: utf-8 -*-

"""
Venus Café - Módulo de Gestão de Cultivares
===========================================

Este módulo permite o registo e a consulta de diferentes cultivares de café
e as suas características agronômicas, servindo como uma base de conhecimento
para a fazenda.
"""

import sqlite3
import logging
from modulos import ui
from database import executar_query, gerar_proximo_codigo_cultivar

def menu_cultivares(usuario: dict, db_path: str):
    """Exibe o menu principal para a gestão de cultivares."""
    contexto = ["Gestão de Cultivares"]
    while True:
        ui.limpar_tela()
        ui.mostrar_logo("Gestão de Cultivares", contexto=contexto)
        
        print("\n[1] Cadastrar Nova Cultivar")
        print("[2] Listar Cultivares")
        print("[3] Visualizar Detalhes de Cultivar")
        if usuario["perfil"] == "admin":
            print("[4] Editar Cultivar")
            print("[5] Excluir Cultivar")
        print("[0] Voltar")
        
        opcao = input("\n>>> Selecione: ").strip()
        
        if opcao == "1": cadastrar_cultivar(db_path)
        elif opcao == "2": listar_cultivares(db_path)
        elif opcao == "3": visualizar_cultivar(db_path)
        elif opcao == "4" and usuario["perfil"] == "admin": editar_cultivar(db_path)
        elif opcao == "5" and usuario["perfil"] == "admin": excluir_cultivar(db_path)
        elif opcao == "0": return
        else: ui.mostrar_erro("Opção inválida!")

def cadastrar_cultivar(db_path: str):
    """Regista uma nova cultivar no banco de dados."""
    contexto = ["Gestão de Cultivares", "Nova"]
    try:
        ui.limpar_tela()
        ui.mostrar_logo("Cadastrar Nova Cultivar", contexto=contexto)
        
        opcoes = {
            "porte": ["Baixo", "Médio", "Alto"], "diametro_copa": ["Pequeno", "Médio", "Grande"],
            "vigor": ["Baixo", "Médio", "Alto"], "maturacao": ["Precoce", "Média-Precoce", "Média", "Média-Tardia", "Tardia"],
            "produtividade": ["Baixa", "Média", "Alta", "Muito Alta"], "tamanho_grao": ["Pequeno", "Médio", "Grande"],
            "qualidade_bebida": ["Regular", "Boa", "Excelente"], "resistencia_ferrugem": ["Suscetível", "Tolerante", "Resistente"],
            "resistencia_nematoide": ["Suscetível", "Resistente"]
        }
        
        print("\n--- Informações Gerais ---")
        codigo = gerar_proximo_codigo_cultivar(db_path)
        nome = input(f"Nome da cultivar (código gerado: {codigo}): ").strip()
        if not nome: ui.mostrar_erro("O nome é obrigatório."); return
        origem = input("Origem: ").strip()
        mantenedor = input("Mantenedor (ex: IAC): ").strip()
        ano_registro = input("Ano de registro (ex: 1999): ").strip()
        
        print("\n--- Características Agronômicas ---")
        porte = ui.selecionar_opcao_de_lista("Porte da planta:", opcoes["porte"], False)
        diametro_copa = ui.selecionar_opcao_de_lista("Diâmetro da copa:", opcoes["diametro_copa"], False)
        vigor = ui.selecionar_opcao_de_lista("Vigor Vegetativo:", opcoes["vigor"], False)
        epoca_maturacao = ui.selecionar_opcao_de_lista("Época de Maturação:", opcoes["maturacao"], False)
        produtividade = ui.selecionar_opcao_de_lista("Produtividade:", opcoes["produtividade"], False)

        print("\n--- Características do Fruto e Grão ---")
        cor_fruto = input("Cor do fruto maduro (ex: Vermelha): ").strip()
        tamanho_grao = ui.selecionar_opcao_de_lista("Tamanho do grão:", opcoes["tamanho_grao"], False)
        cor_folhas = input("Cor das folhas jovens (brotos): ").strip()
        qualidade_bebida = ui.selecionar_opcao_de_lista("Qualidade da bebida:", opcoes["qualidade_bebida"], False)

        print("\n--- Resistência a Pragas e Doenças ---")
        resistencia_ferrugem = ui.selecionar_opcao_de_lista("Resistência à Ferrugem:", opcoes["resistencia_ferrugem"], False)
        resistencia_nematoide = ui.selecionar_opcao_de_lista("Resistência a Nematoide:", opcoes["resistencia_nematoide"], False)
        resistencia_outras = input("Outras resistências (opcional): ").strip()
        
        print("\n--- Considerações Finais ---")
        consideracoes = input("Considerações e recomendações: ").strip()
        
        query = "INSERT INTO cultivares VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)"
        params = (codigo, nome, origem, mantenedor, ano_registro, consideracoes, porte, diametro_copa, vigor, epoca_maturacao, produtividade, cor_fruto, tamanho_grao, cor_folhas, qualidade_bebida, resistencia_ferrugem, resistencia_nematoide, resistencia_outras)
        
        if executar_query(db_path, query, params):
            ui.mostrar_sucesso("Cultivar cadastrada!")
        else: ui.mostrar_erro("Erro ao cadastrar. O nome já pode existir.")
    except sqlite3.IntegrityError:
        ui.mostrar_erro(f"O nome de cultivar '{nome}' já está em uso.")
    except Exception as e:
        logging.error(f"Erro ao cadastrar cultivar: {e}", exc_info=True)
        ui.mostrar_erro(f"Erro inesperado: {e}")

def listar_cultivares(db_path: str):
    """
    Exibe uma lista paginada de todos as cultivares registadas, ordenada
    alfabeticamente por nome.
    """
    contexto = ["Gestão de Cultivares", "Catálogo"]
    titulo = "Catálogo de Cultivares"
    nome_tabela = "cultivares"
    cabecalhos = ["Código", "Nome", "Produtividade", "Maturação", "Res. Ferrugem"]
    larguras = [8, 25, 15, 15, 15]
    colunas_db = ['codigo', 'nome', 'produtividade', 'epoca_maturacao', 'resistencia_ferrugem']
    
    ui.navegacao_paginada(
        db_path, contexto, titulo, nome_tabela, cabecalhos, larguras, colunas_db,
        order_by_clause="nome ASC" # <-- GARANTE A ORDEM ALFABÉTICA
    )


def visualizar_cultivar(db_path: str):
    """Exibe todos os detalhes de uma cultivar específica."""
    contexto = ["Gestão de Cultivares"]
    try:
        selecao = ui.selecionar_entidade(db_path, "Selecione a cultivar para visualizar:", "cultivares", ['codigo', 'nome'])
        if not selecao: return
        codigo_cultivar, nome_cultivar = selecao
        
        query = "SELECT * FROM cultivares WHERE codigo = ?"
        cultivar_res = executar_query(db_path, query, (codigo_cultivar,), fetch=True)
        if not cultivar_res: ui.mostrar_erro("Cultivar não encontrada!"); return
        
        c = cultivar_res[0]
        ui.limpar_tela(); ui.mostrar_logo(f"Detalhes: {nome_cultivar}", contexto=contexto + [nome_cultivar])
        
        print(f"\n{ui.Cores.CIANO}--- Informações Gerais ---{ui.Cores.RESET}")
        print(f"Código: {c[0]} | Nome: {c[1]} | Origem: {c[2]} | Mantenedor: {c[3]} | Ano: {c[4]}")
        print(f"Considerações: {c[5]}")
        print(f"\n{ui.Cores.CIANO}--- Características Agronômicas ---{ui.Cores.RESET}")
        print(f"Porte: {c[6]} | Diâmetro da copa: {c[7]} | Vigor: {c[8]}")
        print(f"Maturação: {c[9]} | Produtividade: {c[10]}")
        print(f"\n{ui.Cores.CIANO}--- Fruto e Grão ---{ui.Cores.RESET}")
        print(f"Cor do fruto: {c[11]} | Tamanho do grão: {c[12]} | Cor folhas jovens: {c[13]}")
        print(f"Qualidade da bebida: {c[14]}")
        print(f"\n{ui.Cores.CIANO}--- Resistências ---{ui.Cores.RESET}")
        print(f"Ferrugem: {c[15]} | Nematoide: {c[16]} | Outras: {c[17]}")
        input("\nPressione Enter para voltar...")
    except Exception as e:
        logging.error(f"Erro ao visualizar cultivar: {e}", exc_info=True); ui.mostrar_erro(f"Erro: {e}")

def editar_cultivar(db_path: str):
    """Modifica os dados de uma cultivar existente."""
    contexto = ["Gestão de Cultivares", "Editar"]
    try:
        selecao = ui.selecionar_entidade(db_path, "Selecione a cultivar a editar:", "cultivares", ['codigo', 'nome'])
        if not selecao: return
        codigo_cultivar, nome_atual = selecao
        
        c = executar_query(db_path, "SELECT * FROM cultivares WHERE codigo = ?", (codigo_cultivar,), fetch=True)[0]
        
        ui.limpar_tela(); ui.mostrar_logo(f"Editando: {nome_atual}", contexto=contexto)
        print("Deixe em branco para manter o valor atual.\n")

        opcoes = {
            "porte": ["Baixo", "Médio", "Alto"], "diametro_copa": ["Pequeno", "Médio", "Grande"],
            "vigor": ["Baixo", "Médio", "Alto"], "maturacao": ["Precoce", "Média-Precoce", "Média", "Média-Tardia", "Tardia"],
            "produtividade": ["Baixa", "Média", "Alta", "Muito Alta"], "tamanho_grao": ["Pequeno", "Médio", "Grande"],
            "qualidade_bebida": ["Regular", "Boa", "Excelente"], "resistencia_ferrugem": ["Suscetível", "Tolerante", "Resistente"],
            "resistencia_nematoide": ["Suscetível", "Resistente"]
        }

        novo_nome = input(f"Nome [{c[1]}]: ").strip() or c[1]
        novo_origem = input(f"Origem [{c[2]}]: ").strip() or c[2]
        novo_mantenedor = input(f"Mantenedor [{c[3]}]: ").strip() or c[3]
        novo_ano = input(f"Ano [{c[4]}]: ").strip() or c[4]
        novo_consideracoes = input(f"Considerações [{c[5]}]: ").strip() or c[5]
        
        novo_porte = ui.selecionar_opcao_de_lista(f"Porte [{c[6]}]:", opcoes["porte"], True) or c[6]
        novo_diametro = ui.selecionar_opcao_de_lista(f"Diâmetro [{c[7]}]:", opcoes["diametro_copa"], True) or c[7]
        novo_vigor = ui.selecionar_opcao_de_lista(f"Vigor [{c[8]}]:", opcoes["vigor"], True) or c[8]
        novo_maturacao = ui.selecionar_opcao_de_lista(f"Maturação [{c[9]}]:", opcoes["maturacao"], True) or c[9]
        novo_produtividade = ui.selecionar_opcao_de_lista(f"Produtividade [{c[10]}]:", opcoes["produtividade"], True) or c[10]

        novo_cor_fruto = input(f"Cor do fruto [{c[11]}]: ").strip() or c[11]
        novo_tamanho_grao = ui.selecionar_opcao_de_lista(f"Tamanho do grão [{c[12]}]:", opcoes["tamanho_grao"], True) or c[12]
        novo_cor_folhas = input(f"Cor folhas jovens [{c[13]}]: ").strip() or c[13]
        novo_qualidade_bebida = ui.selecionar_opcao_de_lista(f"Qualidade bebida [{c[14]}]:", opcoes["qualidade_bebida"], True) or c[14]

        novo_res_ferrugem = ui.selecionar_opcao_de_lista(f"Res. Ferrugem [{c[15]}]:", opcoes["resistencia_ferrugem"], True) or c[15]
        novo_res_nematoide = ui.selecionar_opcao_de_lista(f"Res. Nematoide [{c[16]}]:", opcoes["resistencia_nematoide"], True) or c[16]
        novo_res_outras = input(f"Outras res. [{c[17]}]: ").strip() or c[17]
        
        query = "UPDATE cultivares SET nome=?, origem=?, mantenedor=?, ano_registro=?, consideracoes=?, porte=?, diametro_copa=?, vigor=?, epoca_maturacao=?, produtividade=?, cor_fruto_maduro=?, tamanho_grao=?, cor_folhas_jovens=?, qualidade_bebida=?, resistencia_ferrugem=?, resistencia_nematoide=?, resistencia_outras=? WHERE codigo=?"
        params = (novo_nome, novo_origem, novo_mantenedor, novo_ano, novo_consideracoes, novo_porte, novo_diametro, novo_vigor, novo_maturacao, novo_produtividade, novo_cor_fruto, novo_tamanho_grao, novo_cor_folhas, novo_qualidade_bebida, novo_res_ferrugem, novo_res_nematoide, novo_res_outras, codigo_cultivar)
        
        if executar_query(db_path, query, params):
            ui.mostrar_sucesso("Cultivar atualizada!")
        else: ui.mostrar_erro("Falha ao atualizar cultivar.")
    except Exception as e:
        logging.error(f"Erro ao editar cultivar: {e}", exc_info=True)
        ui.mostrar_erro(f"Erro ao editar cultivar: {e}")

def excluir_cultivar(db_path: str):
    """Remove uma cultivar do banco de dados, se não estiver em uso."""
    contexto = ["Gestão de Cultivares", "Excluir"]
    try:
        ui.limpar_tela(); ui.mostrar_logo("Excluir Cultivar", contexto=contexto)
        selecao = ui.selecionar_entidade(db_path, "Selecione a cultivar a excluir:", "cultivares", ['codigo', 'nome'])
        if not selecao: return
        codigo, nome = selecao
        
        em_uso_t = executar_query(db_path, "SELECT COUNT(*) FROM talhoes WHERE cultivar_codigo_padrao=?", (codigo,), fetch=True)[0][0]
        em_uso_l = executar_query(db_path, "SELECT COUNT(*) FROM linhas WHERE cultivar_codigo=?", (codigo,), fetch=True)[0][0]
        em_uso_p = executar_query(db_path, "SELECT COUNT(*) FROM plantas WHERE cultivar_codigo=?", (codigo,), fetch=True)[0][0]
        total_usos = em_uso_t + em_uso_l + em_uso_p
        if total_usos > 0:
            ui.mostrar_erro(f"'{nome}' não pode ser excluída, pois está em uso por {total_usos} registo(s).")
            return

        confirmar = input(f"Digite 'CONFIRMAR' para excluir '{nome}': ").strip()
        if confirmar == 'CONFIRMAR':
            if executar_query(db_path, "DELETE FROM cultivares WHERE codigo = ?", (codigo,)):
                ui.mostrar_sucesso("Cultivar excluída com sucesso!")
            else: ui.mostrar_erro("Falha ao excluir cultivar")
        else: ui.mostrar_alerta("Exclusão cancelada.")
    except Exception as e:
        logging.error(f"Erro ao excluir cultivar: {e}", exc_info=True)
        ui.mostrar_erro(f"Erro ao excluir cultivar: {e}")
