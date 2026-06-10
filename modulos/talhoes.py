# -*- coding: utf-8 -*-

"""
Venus Café - Módulo de Gestão de Talhões, Linhas e Plantas
==========================================================

Este módulo contém toda a lógica para o CRUD (Create, Read, Update, Delete)
da hierarquia física da fazenda: Talhões > Linhas > Plantas.
"""

import sqlite3
import logging
import re
import time
from datetime import datetime
from modulos import ui
import database 
from database import executar_query, gerar_proximo_codigo_talhao

# --- Menus Principais da Hierarquia ---

def menu_talhoes(usuario: dict, db_path: str):
    """Menu principal para a gestão de talhões."""
    contexto = ["Gestão de Talhões"]
    while True:
        ui.limpar_tela()
        ui.mostrar_logo("Gestão de Talhões", contexto=contexto)
        print("\n[1] Cadastrar Novo Talhão")
        print("[2] Listar Talhões")
        if usuario["perfil"] == "admin":
            print("[3] Editar Talhão")
            print("[4] Excluir Talhão")
        print("[5] Gerenciar Linhas de um Talhão")
        print("[0] Voltar")
        
        opcao = input("\n>>> Selecione: ").strip()
        if opcao == "1": cadastrar_talhao(db_path)
        elif opcao == "2": listar_talhoes(db_path)
        elif opcao == "3" and usuario["perfil"] == "admin": editar_talhao(db_path)
        elif opcao == "4" and usuario["perfil"] == "admin": excluir_talhao(db_path)
        elif opcao == "5": gerenciar_linhas_talhao(db_path, usuario, contexto)
        elif opcao == "0": return
        else: ui.mostrar_erro("Opção inválida!")

def menu_linhas(talhao_codigo: str, db_path: str, usuario: dict, contexto: list):
    """Menu para gestão de linhas de um talhão específico."""
    while True:
        ui.limpar_tela()
        ui.mostrar_logo(f"Gestão de Linhas", contexto=contexto)
        print("\n[1] Cadastrar Nova Linha")
        print("[2] Listar Linhas")
        if usuario["perfil"] == "admin":
            print("[3] Editar Linha")
            print("[4] Excluir Linha")
        print("[5] Gerenciar Plantas de uma Linha")
        print("[0] Voltar")
        
        opcao = input("\n>>> Selecione: ").strip()
        if opcao == "1": cadastrar_linha(talhao_codigo, db_path, contexto)
        elif opcao == "2": listar_linhas(talhao_codigo, db_path, contexto)
        elif opcao == "3" and usuario["perfil"] == "admin": editar_linha(talhao_codigo, db_path, contexto)
        elif opcao == "4" and usuario["perfil"] == "admin": excluir_linha(talhao_codigo, db_path)
        elif opcao == "5": gerenciar_plantas_linha(talhao_codigo, db_path, usuario, contexto)
        elif opcao == "0": return
        else: ui.mostrar_erro("Opção inválida!")

def menu_plantas(linha_id: int, db_path: str, usuario: dict, contexto: list):
    """Menu para gestão de plantas de uma linha específica."""
    while True:
        try:
            ui.limpar_tela()
            ui.mostrar_logo("Gestão de Plantas", contexto=contexto)
            print("\n[1] Cadastrar Nova Planta")
            print("[2] Listar Plantas")
            print("[3] Registrar Substituição")
            if usuario["perfil"] == "admin":
                print("[4] Editar Planta")
                print("[5] Excluir Planta")
            print("[0] Voltar")
            
            opcao = input("\n>>> Selecione: ").strip()
            if not usuario["perfil"] == "admin" and opcao in ["4", "5"]:
                ui.mostrar_erro("Apenas administradores podem executar esta ação."); continue
            
            if opcao == "1": cadastrar_planta(linha_id, db_path, contexto)
            elif opcao == "2": listar_plantas(linha_id, db_path, contexto)
            elif opcao == "3": substituir_planta(linha_id, db_path, contexto)
            elif opcao == "4": editar_planta(linha_id, db_path, contexto)
            elif opcao == "5": excluir_planta(linha_id, db_path)
            elif opcao == "0": return
            else: ui.mostrar_erro("Opção inválida!")
        except Exception as e:
            logging.error(f"Erro no menu de plantas: {e}", exc_info=True)
            ui.mostrar_erro(f"Erro inesperado: {e}")

# --- Funções de Portais (Navegação) ---

def gerenciar_linhas_talhao(db_path: str, usuario: dict, contexto_pai: list):
    """Portal para selecionar um talhão e entrar na gestão de suas linhas."""
    selecao = ui.selecionar_entidade(db_path, "Selecione o talhão:", "talhoes", ['codigo', 'nome'])
    if not selecao: return
    codigo_talhao, nome_talhao = selecao
    novo_contexto = contexto_pai + [f"Talhão {nome_talhao}"]
    menu_linhas(codigo_talhao, db_path, usuario, novo_contexto)

def gerenciar_plantas_linha(talhao_codigo: str, db_path: str, usuario: dict, contexto_pai: list):
    """Portal para selecionar uma linha e entrar na gestão de suas plantas."""
    where = ("talhao_codigo = ?", [talhao_codigo])
    selecao = ui.selecionar_entidade(db_path, "Selecione a linha:", "linhas", ['id', 'numero'], where)
    if not selecao: return
    linha_id, numero_linha = selecao
    novo_contexto = contexto_pai + [f"Linha {numero_linha}"]
    menu_plantas(linha_id, db_path, usuario, novo_contexto)

def cadastrar_talhao(db_path: str):
    """Regista um novo talhão no banco de dados, incluindo coordenadas e altitude."""
    contexto = ["Gestão de Talhões", "Novo Talhão"]
    try:
        ui.limpar_tela()
        ui.mostrar_logo("Cadastrar Novo Talhão", contexto=contexto)
        
        codigo = gerar_proximo_codigo_talhao(db_path)
        print(f"\nCódigo gerado automaticamente: {codigo}")
        
        nome = input("Nome do talhão: ").strip()
        if not nome:
            ui.mostrar_erro("O nome é obrigatório."); return

        print("\n--- Localização (Opcional) ---")
        latitude = ui.obter_coordenada("Latitude do talhão:", 'latitude')
        longitude = ui.obter_coordenada("Longitude do talhão:", 'longitude')
        
        print("\n--- Detalhes Agronômicos ---")
        espacamento = ui.obter_numero_positivo("Espaçamento entre linhas (m): ")
        if espacamento is None:
            ui.mostrar_erro("O espaçamento é obrigatório."); return
            
        altitude_media = ui.obter_numero_positivo("Altitude média do talhão (m): ", permitir_vazio=True)
        consideracoes = input("Considerações/observações: ").strip()
        
        cultivar_padrao = None
        if input("\nDeseja definir um cultivar padrão? (s/n): ").lower() == 's':
            selecao = ui.selecionar_entidade(db_path, "Selecione o cultivar padrão:", "cultivares", ['codigo', 'nome'])
            if selecao:
                cultivar_padrao, _ = selecao
            
        query = "INSERT INTO talhoes (codigo, nome, latitude, longitude, espacamento_linha, consideracoes, cultivar_codigo_padrao, altitude_media) VALUES (?, ?, ?, ?, ?, ?, ?, ?)"
        params = (codigo, nome, latitude, longitude, espacamento, consideracoes, cultivar_padrao, altitude_media)
        
        if executar_query(db_path, query, params):
            ui.mostrar_sucesso(f"Talhão {codigo} cadastrado!")
        else:
            ui.mostrar_erro("Erro ao cadastrar talhão")
            
    except Exception as e:
        logging.error(f"Erro ao cadastrar talhão: {e}", exc_info=True)
        ui.mostrar_erro(f"Erro: {e}")

def listar_talhoes(db_path: str):
    """
    Exibe uma lista paginada de todos os talhões, ordenada pelo código do talhão.
    """
    contexto = ["Gestão de Talhões", "Listagem"]
    
    cabecalhos = ["Código", "Nome", "Nº Plantas", "Espaç. (m)", "Altitude (m)", "Cultivar Padrão"]
    larguras = [7, 20, 12, 12, 14, 20]
    colunas_db = [
        't.codigo', 't.nome', 'COUNT(p.id)', 
        't.espacamento_linha', 't.altitude_media', 'c.nome'
    ]
    
    join_clause = """
    LEFT JOIN cultivares c ON t.cultivar_codigo_padrao = c.codigo
    LEFT JOIN linhas l ON t.codigo = l.talhao_codigo
    LEFT JOIN plantas p ON l.id = p.linha_id AND p.status = 'ativa'
    """
    
    group_by_clause = "t.codigo, t.nome, c.nome, t.espacamento_linha, t.altitude_media"

    ui.navegacao_paginada(
        db_path, contexto, "Resumo de Talhões", "talhoes t",
        cabecalhos, larguras, colunas_db,
        join_clause=join_clause,
        group_by_clause=group_by_clause,
        order_by_clause="t.codigo ASC"
    )


def editar_talhao(db_path: str):
    """Modifica os dados de um talhão existente, incluindo a altitude média."""
    contexto = ["Gestão de Talhões", "Editar"]
    try:
        selecao = ui.selecionar_entidade(db_path, "Selecione o talhão a editar:", "talhoes", ['codigo', 'nome'])
        if not selecao: return
        codigo_talhao, nome_talhao = selecao
        dados = executar_query(db_path, "SELECT * FROM talhoes WHERE codigo = ?", (codigo_talhao,), fetch=True)[0]
        ui.limpar_tela(); ui.mostrar_logo(f"Editando Talhão {nome_talhao}", contexto=contexto)
        print("Deixe em branco para manter o valor atual\n")
        novo_nome = input(f"Nome [{dados[1]}]: ").strip() or dados[1]
        print("\n--- Localização (Opcional) ---")
        nova_lat = ui.obter_coordenada("Latitude:", 'latitude', valor_atual=dados[2])
        nova_lon = ui.obter_coordenada("Longitude:", 'longitude', valor_atual=dados[3])
        print("\n--- Detalhes Agronômicos ---")
        novo_esp = ui.obter_numero_positivo(f"Espaçamento (m) [{dados[4]}]: ", permitir_vazio=True) or dados[4]
        nova_alt = ui.obter_numero_positivo(f"Altitude média (m) [{dados[7] or 'N/D'}]: ", permitir_vazio=True) or dados[7]
        novas_cons = input(f"Considerações [{dados[5] or ''}]: ").strip() or dados[5]
        cultivar_atual = dados[6]
        if input(f"\nCultivar Padrão: {cultivar_atual or 'Nenhum'}. Alterar? (s/n): ").lower() == 's':
            sel_cult = ui.selecionar_entidade(db_path, "Novo cultivar padrão:", "cultivares", ['codigo', 'nome'])
            novo_cultivar = sel_cult[0] if sel_cult else cultivar_atual
        else: novo_cultivar = cultivar_atual
        query = "UPDATE talhoes SET nome=?, latitude=?, longitude=?, espacamento_linha=?, consideracoes=?, cultivar_codigo_padrao=?, altitude_media=? WHERE codigo=?"
        params = (novo_nome, nova_lat, nova_lon, novo_esp, novas_cons, novo_cultivar, nova_alt, codigo_talhao)
        if executar_query(db_path, query, params): ui.mostrar_sucesso("Talhão atualizado!")
        else: ui.mostrar_erro("Falha ao atualizar talhão")
    except Exception as e: ui.mostrar_erro(f"Erro ao editar talhão: {e}")

def excluir_talhao(db_path: str):
    """
    Remove um talhão, se não houver dependências em linhas, atividades ou análises.
    """
    try:
        selecao = ui.selecionar_entidade(db_path, "Selecione o talhão a excluir:", "talhoes", ['codigo', 'nome'])
        if not selecao: return
        codigo_talhao, nome_talhao = selecao

        # Verificação de dependência 1: Atividades
        atividades = executar_query(db_path, "SELECT COUNT(*) FROM registros_atividades WHERE talhao_codigo=?", (codigo_talhao,), fetch=True)[0][0]
        if atividades > 0:
            ui.mostrar_erro(f"'{nome_talhao}' não pode ser excluído, pois possui {atividades} atividade(s) no histórico.");
            input("\nPressione Enter para continuar..."); return

        # Verificação de dependência 2: Linhas
        linhas = executar_query(db_path, "SELECT COUNT(*) FROM linhas WHERE talhao_codigo=?", (codigo_talhao,), fetch=True)[0][0]
        if linhas > 0:
            ui.mostrar_erro(f"'{nome_talhao}' não pode ser excluído, pois possui {linhas} linha(s).");
            input("\nPressione Enter para continuar..."); return
        # Verificação de dependência 3: Análises
        analises = executar_query(db_path, "SELECT COUNT(*) FROM analises WHERE talhao_codigo_associado=?", (codigo_talhao,), fetch=True)[0][0]
        if analises > 0:
            ui.mostrar_erro(f"'{nome_talhao}' não pode ser excluído, pois possui {analises} análise(s) associada(s).");
            input("\nPressione Enter para continuar..."); return

        # Se passou por todas as verificações, pede confirmação final
        if input(f"\nConfirmar exclusão de '{nome_talhao}'? (s/n): ").lower() == 's':
            if executar_query(db_path, "DELETE FROM talhoes WHERE codigo = ?", (codigo_talhao,)):
                ui.mostrar_sucesso("Talhão excluído com sucesso!")
            else:
                ui.mostrar_erro("Falha ao excluir talhão")
        else:
            ui.mostrar_alerta("Exclusão cancelada!")
            
    except Exception as e:
        logging.error(f"Erro ao excluir talhão: {e}", exc_info=True)
        ui.mostrar_erro(f"Erro ao excluir talhão: {e}")


def cadastrar_linha(talhao_codigo: str, db_path: str, contexto_pai: list):
    """Regista uma nova linha e todas as suas plantas de uma só vez, com validações e limites."""
    contexto = contexto_pai + ["Nova Linha"]
    try:
        ui.limpar_tela()
        ui.mostrar_logo("Cadastrar Linha", contexto=contexto)
        
        numero_linha = ui.obter_numero_positivo("Número da nova linha: ", tipo_dado=int)
        if numero_linha is None:
            ui.mostrar_erro("Número da linha é obrigatório."); return
        
        existe = executar_query(db_path, "SELECT id FROM linhas WHERE talhao_codigo = ? AND numero = ?", (talhao_codigo, numero_linha), fetch=True)
        if existe:
            ui.mostrar_erro(f"A linha {numero_linha} já existe neste talhão."); return

        quantidade_plantas = ui.obter_numero_positivo("Quantidade de plantas: ", tipo_dado=int)
        if quantidade_plantas is None:
            ui.mostrar_erro("Quantidade é obrigatória."); return
        LIMITE_MAX_PLANTAS = 20000 # Limite generoso para uma única operação
        if quantidade_plantas > LIMITE_MAX_PLANTAS:
            ui.mostrar_erro(f"O número de plantas ({quantidade_plantas}) excede o limite de segurança ({LIMITE_MAX_PLANTAS}).")
            ui.mostrar_alerta("Se precisa de registar mais plantas, por favor, faça-o em operações separadas.")
            return

        espacamento_planta = ui.obter_numero_positivo("Espaçamento entre plantas (m): ")
        if espacamento_planta is None:
            ui.mostrar_erro("Espaçamento é obrigatório."); return

        data_plantio = ui.obter_data_valida("Data de plantio")
        
        cultivar_codigo, nome_cultivar = None, "Não Definido"
        if input("\nDeseja definir um cultivar para a linha? (s/n): ").lower() == 's':
            selecao = ui.selecionar_entidade(db_path, "Selecione o cultivar:", "cultivares", ['codigo', 'nome'])
            if selecao: cultivar_codigo, nome_cultivar = selecao
        
        ui.limpar_tela(); ui.mostrar_logo("Confirmar Cadastro", contexto=contexto)
        print(f"\nTalhão: {talhao_codigo}, Linha: {numero_linha}")
        print(f"Plantas: {quantidade_plantas}, Espaçamento: {espacamento_planta}m")
        print(f"Data de Plantio: {datetime.strptime(data_plantio, '%Y-%m-%d').strftime('%d/%m/%Y') if data_plantio else 'N/D'}")
        print(f"Cultivar: {nome_cultivar}")
        if input("\nConfirmar cadastro? (s/n): ").lower() != 's':
            ui.mostrar_alerta("Cadastro cancelado!"); return

        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        try:
            codigo_linha = f"L{numero_linha}"
            cursor.execute("INSERT INTO linhas (codigo, talhao_codigo, numero, quantidade_plantas, cultivar_codigo, espacamento_planta) VALUES (?, ?, ?, ?, ?, ?)", (codigo_linha, talhao_codigo, numero_linha, quantidade_plantas, cultivar_codigo, espacamento_planta))
            linha_id = cursor.lastrowid
            
            codigo_inicial_str = database.gerar_proximo_codigo_planta_no_talhao(db_path, talhao_codigo)
            numeros_encontrados = re.findall(r'\d+', codigo_inicial_str)
            if not numeros_encontrados: raise ValueError(f"Não foi possível extrair número do código '{codigo_inicial_str}'")
            numero_base = int(numeros_encontrados[0])
            
            plantas_para_inserir = []
            for i in range(quantidade_plantas):
                codigo_planta_atual = f"P{numero_base + i}"
                plantas_para_inserir.append((codigo_planta_atual, linha_id, i + 1, cultivar_codigo, data_plantio, 'ativa'))
            
            cursor.executemany("INSERT INTO plantas (codigo, linha_id, numero_na_linha, cultivar_codigo, data_plantio, status) VALUES (?, ?, ?, ?, ?, ?)", plantas_para_inserir)
            conn.commit()
            ui.mostrar_sucesso(f"Linha {codigo_linha} e {len(plantas_para_inserir)} plantas cadastradas!")
        except Exception as e:
            conn.rollback(); raise e
        finally:
            conn.close()
    except Exception as e:
        logging.error(f"Erro ao cadastrar linha: {e}", exc_info=True)
        ui.mostrar_erro(f"Ocorreu um erro: {e}")

def listar_linhas(talhao_codigo: str, db_path: str, contexto: list):
    """
    Exibe uma lista paginada das linhas de um talhão, ordenada pelo número da linha.
    """
    ui.navegacao_paginada(
        db_path, contexto, f"Linhas do Talhão {talhao_codigo}", "linhas l",
        ["Código", "Número", "Cultivar", "Qtd. Plantas", "Espaçamento"],
        [7, 8, 25, 16, 15],
        ['l.codigo', 'l.numero', 'c.nome', 'l.quantidade_plantas', 'l.espacamento_planta || " m"'],
        join_clause="LEFT JOIN cultivares c ON l.cultivar_codigo = c.codigo",
        where_clause=("l.talhao_codigo = ?", [talhao_codigo]),
        order_by_clause="l.numero ASC"
    )

def editar_linha(talhao_codigo: str, db_path: str, contexto: list):
    """Modifica os dados de uma linha existente e propaga as alterações para as plantas."""
    try:
        where = ("talhao_codigo = ?", [talhao_codigo])
        selecao = ui.selecionar_entidade(db_path, "Selecione a linha a editar:", "linhas", ['id', 'numero'], where)
        if not selecao: return
        
        linha_id, numero_atual = selecao
        
        # Query para obter os dados atuais da linha
        query = "SELECT l.numero, l.cultivar_codigo, (SELECT p.data_plantio FROM plantas p WHERE p.linha_id=l.id LIMIT 1) as data FROM linhas l WHERE l.id=?"
        dados = executar_query(db_path, query, (linha_id,), fetch=True)
        if not dados:
            ui.mostrar_erro("Dados da linha não encontrados.")
            return
            
        linha_atual = dados[0]
        
        contexto_edicao = contexto + [f"Editar Linha {numero_atual}"]
        ui.limpar_tela()
        ui.mostrar_logo(f"Editando Linha {numero_atual}", contexto=contexto_edicao)
        
        print("\nDeixe em branco para manter o valor atual.")
        
        # Coleta dos novos dados
        novo_numero = ui.obter_numero_positivo(f"Número da linha [{linha_atual[0]}]: ", int, True) or linha_atual[0]
        novo_cultivar = input(f"Cód. cultivar [{linha_atual[1] or 'N/D'}]: ").strip() or linha_atual[1]
        nova_data = ui.obter_data_valida(f"Data de plantio [{linha_atual[2] or ''}]: ", default_hoje=False) or linha_atual[2]

        # --- INÍCIO DA CORREÇÃO ---
        # A lógica foi reestruturada para garantir que as alterações sejam propagadas.

        query_linha = "UPDATE linhas SET numero=?, cultivar_codigo=? WHERE id=?"
        params_linha = (int(novo_numero), novo_cultivar, linha_id)

        # 1. Primeiro, tenta atualizar a tabela 'linhas'
        if executar_query(db_path, query_linha, params_linha):
            
            # 2. Se a atualização da linha deu certo, propaga a mudança da cultivar para todas as plantas filhas
            if novo_cultivar != linha_atual[1]: # Só executa se a cultivar realmente mudou
                ui.mostrar_alerta("A atualizar a cultivar em todas as plantas da linha...")
                executar_query(db_path, "UPDATE plantas SET cultivar_codigo=? WHERE linha_id=?", (novo_cultivar, linha_id))

            # 3. Atualiza a data de plantio das plantas, se uma nova data foi fornecida
            if nova_data:
                executar_query(db_path, "UPDATE plantas SET data_plantio=? WHERE linha_id=?", (nova_data, linha_id))

            ui.mostrar_sucesso("Linha e plantas associadas foram atualizadas com sucesso!")

        else:
            # Se a atualização principal (na linha) falhar, informa o erro.
            ui.mostrar_erro("Falha ao atualizar os dados da linha.")
        # --- FIM DA CORREÇÃO ---

    except Exception as e:
        logging.error(f"Erro ao editar linha: {e}", exc_info=True)
        ui.mostrar_erro(f"Ocorreu um erro inesperado: {e}")


def excluir_linha(talhao_codigo: str, db_path: str):
    """Remove uma linha e todas as suas plantas associadas."""
    try:
        where = ("talhao_codigo = ?", [talhao_codigo])
        selecao = ui.selecionar_entidade(db_path, "Selecione a linha a EXCLUIR:", "linhas", ['id', 'numero'], where)
        if not selecao: return
        linha_id, numero_linha = selecao
        confirmar = input(f"\nExcluir a linha {numero_linha} e TODAS as suas plantas? (s/n): ").lower()
        if confirmar != 's': ui.mostrar_alerta("Exclusão cancelada."); return
        if executar_query(db_path, "DELETE FROM linhas WHERE id = ?", (linha_id,)):
            ui.mostrar_sucesso("Linha e plantas associadas foram excluídas!")
        else: ui.mostrar_erro("Falha ao excluir a linha.")
    except Exception as e:
        logging.error(f"Erro ao excluir linha: {e}", exc_info=True); ui.mostrar_erro(f"Erro: {e}")

def cadastrar_planta(linha_id: int, db_path: str, contexto: list, numero_planta: int = None):
    """Regista uma única planta nova numa linha."""
    contexto_novo = contexto + ["Nova Planta"]
    try:
        ui.limpar_tela(); ui.mostrar_logo("Cadastrar Nova Planta", contexto=contexto_novo)
        if numero_planta is None:
            num_planta = ui.obter_numero_positivo("Número da planta na linha: ", tipo_dado=int)
            if num_planta is None: ui.mostrar_erro("O número é obrigatório."); return
        else:
            num_planta = numero_planta; print(f"\nPosição para substituição: {num_planta}")
        query_linha = "SELECT talhao_codigo FROM linhas WHERE id = ?"
        talhao_codigo = executar_query(db_path, query_linha, (linha_id,), fetch=True)[0][0]
        codigo_planta = database.gerar_proximo_codigo_planta_no_talhao(db_path, talhao_codigo)
        cultivar_codigo = None
        if input("Deseja associar um cultivar? (s/n): ").lower() == 's':
            selecao = ui.selecionar_entidade(db_path, "Selecione o cultivar:", "cultivares", ['codigo', 'nome'])
            if selecao: cultivar_codigo, _ = selecao
        data_plantio = ui.obter_data_valida("Data de plantio", default_hoje=False)
        observacoes = input("Observações (opcional): ").strip() or None
        if input("\nConfirmar cadastro? (s/n): ").lower() != 's': ui.mostrar_alerta("Cadastro cancelado!"); return
        query_insert = "INSERT INTO plantas (codigo, linha_id, numero_na_linha, cultivar_codigo, data_plantio, observacoes) VALUES (?, ?, ?, ?, ?, ?)"
        params = (codigo_planta, linha_id, num_planta, cultivar_codigo, data_plantio, observacoes)
        if executar_query(db_path, query_insert, params): ui.mostrar_sucesso(f"Planta {codigo_planta} cadastrada!")
        else: ui.mostrar_erro("Falha ao cadastrar a planta.")
    except sqlite3.IntegrityError: ui.mostrar_erro(f"Já existe uma planta na posição {num_planta} desta linha.")
    except Exception as e:
        logging.error(f"Erro no cadastro de planta: {e}", exc_info=True); ui.mostrar_erro(f"Ocorreu um erro: {e}")

def listar_plantas(linha_id: int, db_path: str, contexto: list):
    """Exibe uma lista paginada das plantas ativas de uma linha e o histórico."""
    ui.navegacao_paginada(
        db_path, contexto, "Plantas Ativas", "plantas p",
        ["Código", "Posição", "Cultivar", "Plantio", "Substituta"],
        [8, 8, 20, 12, 10],
        ['p.codigo', 'p.numero_na_linha', 'c.nome', 'p.data_plantio', "CASE WHEN p.substituta THEN 'Sim' ELSE 'Não' END"],
        join_clause="LEFT JOIN cultivares c ON p.cultivar_codigo = c.codigo",
        where_clause=("p.linha_id = ? AND p.status = 'ativa'", [linha_id])
    )
    query_inativas = "SELECT codigo, numero_na_linha, observacoes FROM plantas WHERE linha_id = ? AND status = 'inativa' ORDER BY numero_na_linha"
    plantas_inativas = executar_query(db_path, query_inativas, (linha_id,), fetch=True)
    if plantas_inativas:
        print(f"\n{ui.Cores.AMARELO}--- Histórico de Plantas Substituídas ({len(plantas_inativas)}) ---{ui.Cores.RESET}")
        ui.mostrar_tabela(["Código Antigo", "Posição", "Observações"], plantas_inativas, [15, 8, 60])
        input("\nPressione Enter para voltar ao menu...")

def substituir_planta(linha_id: int, db_path: str, contexto: list):
    """Regista a substituição de uma planta usando uma transação para garantir a integridade."""
    contexto_novo = contexto + ["Substituir"]
    
    ui.limpar_tela()
    ui.mostrar_logo("Substituir Planta", contexto=contexto_novo)
    
    where = ("linha_id = ? AND status = 'ativa'", [linha_id])
    selecao = ui.selecionar_entidade(db_path, "Planta a ser substituída:", "plantas", ['id', 'codigo', 'numero_na_linha'], where)
    if not selecao: 
        return
        
    planta_id_original, codigo_original, pos_na_linha = selecao
    
    motivo = input("\nMotivo da substituição: ").strip()
    if not motivo:
        ui.mostrar_erro("O motivo é obrigatório!")
        return
        
    numeros = re.findall(r'^P(\d+)', codigo_original)
    if not numeros:
        ui.mostrar_erro("Código da planta inválido.")
        return
    posicao_base = numeros[0]
    query_contagem = f"SELECT COUNT(*) FROM plantas WHERE linha_id=? AND (codigo LIKE 'P{posicao_base}S%' OR codigo = 'P{posicao_base}')"
    contador_substituicao = executar_query(db_path, query_contagem, (linha_id,), fetch=True)[0][0]
    novo_codigo = f"P{posicao_base}S{contador_substituicao}"

    print("\n--- Cadastro da Nova Planta (Substituta) ---")
    data_plantio_nova = ui.obter_data_valida("Data de plantio da nova muda", default_hoje=True)
    if not data_plantio_nova:
        ui.mostrar_alerta("Data de plantio é obrigatória. Operação cancelada.")
        return
    conn = None
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        obs_query = executar_query(db_path, "SELECT observacoes FROM plantas WHERE id=?", (planta_id_original,), fetch=True)
        obs_original = obs_query[0][0] if obs_query and obs_query[0] else ""
        obs_atualizada = f"{obs_original or ''}\n[SUBSTITUÍDA em {datetime.now().strftime('%d/%m/%Y')}] Motivo: {motivo}"
        cursor.execute("UPDATE plantas SET status='inativa', observacoes=? WHERE id=?", (obs_atualizada, planta_id_original))
        query_insert = "INSERT INTO plantas (codigo, linha_id, numero_na_linha, data_plantio, status, substituta, observacoes) VALUES (?, ?, ?, ?, 'ativa', 1, ?)"
        params_insert = (novo_codigo, linha_id, pos_na_linha, data_plantio_nova, f"Substituta de {codigo_original}")
        cursor.execute(query_insert, params_insert)
        conn.commit()
        ui.mostrar_sucesso(f"Planta {codigo_original} aposentada. Nova planta {novo_codigo} registrada com sucesso!")

    except sqlite3.Error as e:
        # Passo 4: Se qualquer erro ocorrer, desfazer TODAS as alterações
        if conn:
            conn.rollback()
        logging.error(f"Erro na transação de substituição de planta: {e}", exc_info=True)
        ui.mostrar_erro(f"Falha ao registrar a nova planta. A operação foi cancelada para proteger os dados. Erro: {e}")
        
    finally:
        # Passo 5: Fechar a conexão
        if conn:
            conn.close()
    # --- FIM DA CORREÇÃO ---


def editar_planta(linha_id: int, db_path: str, contexto: list):
    """Modifica os dados de uma planta existente."""
    contexto_novo = contexto + ["Editar Planta"]
    try:
        ui.limpar_tela(); ui.mostrar_logo("Editar Informações de Planta", contexto=contexto_novo)
        query_ativas = "SELECT id, codigo, numero_na_linha FROM plantas WHERE linha_id = ? AND status = 'ativa' ORDER BY numero_na_linha"
        plantas_ativas = executar_query(db_path, query_ativas, (linha_id,), fetch=True)
        print(f"\n{ui.Cores.VERDE}--- Plantas Ativas ---{ui.Cores.RESET}")
        if not plantas_ativas: ui.mostrar_alerta("Nenhuma planta ativa.")
        else:
            for i, planta in enumerate(plantas_ativas, 1): print(f"  {i}. Cód: {planta[1]} (Pos: {planta[2]})")
        query_inativas = "SELECT id, codigo, numero_na_linha FROM plantas WHERE linha_id = ? AND status = 'inativa' ORDER BY numero_na_linha"
        plantas_inativas = executar_query(db_path, query_inativas, (linha_id,), fetch=True)
        if plantas_inativas:
            print(f"\n{ui.Cores.AMARELO}--- Histórico de Inativas ---{ui.Cores.RESET}")
            offset = len(plantas_ativas)
            for i, planta in enumerate(plantas_inativas, 1): print(f"{ui.Cores.VERMELHO}  {i+offset}. Cód: {planta[1]} (Pos: {planta[2]}){ui.Cores.RESET}")
        todas_as_plantas = plantas_ativas + plantas_inativas
        if not todas_as_plantas: input("\nNenhuma planta para editar. Enter..."); return
        try:
            escolha = int(input("\nDigite o número da planta: ").strip())
            if not (1 <= escolha <= len(todas_as_plantas)): ui.mostrar_erro("Seleção inválida!"); return
            planta_id = todas_as_plantas[escolha - 1][0]
        except ValueError: ui.mostrar_erro("Digite um número!"); return
        planta_db = executar_query(db_path, "SELECT codigo, numero_na_linha, cultivar_codigo, data_plantio, observacoes, status FROM plantas WHERE id = ?", (planta_id,), fetch=True)[0]
        codigo, num, cultivar, data, obs, status = planta_db
        ui.limpar_tela(); ui.mostrar_logo(f"Editando Planta: {codigo}", contexto=contexto_novo)
        print("\nDeixe em branco para manter.")
        novo_codigo = input(f"Código [{codigo}]: ").strip() or codigo
        novo_num = ui.obter_numero_positivo(f"Número na linha [{num}]: ", tipo_dado=int, permitir_vazio=True) or num
        novo_cultivar = input(f"Cultivar [{cultivar or 'N/D'}]: ").strip() or cultivar
        nova_data = ui.obter_data_valida(f"Data de plantio [{data or 'N/I'}]: ", default_hoje=False) or data
        novas_obs = input(f"Observações [{obs or 'Nenhuma'}]: ").strip() or obs
        novo_status = status
        if status == 'inativa' and input("Deseja reativar? (s/n): ").lower() == 's': novo_status = 'ativa'
        query_update = "UPDATE plantas SET codigo=?, numero_na_linha=?, cultivar_codigo=?, data_plantio=?, observacoes=?, status=? WHERE id=?"
        params = (novo_codigo, int(novo_num), novo_cultivar, nova_data, novas_obs, novo_status, planta_id)
        if executar_query(db_path, query_update, params): ui.mostrar_sucesso("Planta atualizada!")
        else: ui.mostrar_erro("Falha ao atualizar a planta.")
    except Exception as e:
        logging.error(f"Erro ao editar planta: {e}", exc_info=True); ui.mostrar_erro(f"Ocorreu um erro: {e}")

def excluir_planta(linha_id: int, db_path: str):
    """Remove o registo de uma planta."""
    try:
        where = ("linha_id = ?", [linha_id])
        selecao = ui.selecionar_entidade(db_path, "Planta a ser EXCLUÍDA:", "plantas", ['id', 'codigo', 'status'], where)
        if not selecao: return
        planta_id, codigo_planta, _ = selecao
        confirmar = input(f"Confirmar exclusão da planta '{codigo_planta}'? (s/n): ").lower()
        if confirmar != 's': ui.mostrar_alerta("Exclusão cancelada!"); return
        if executar_query(db_path, "DELETE FROM plantas WHERE id = ?", (planta_id,)): ui.mostrar_sucesso("Planta excluída!")
        else: ui.mostrar_erro("Erro ao excluir planta")
    except Exception as e:
        logging.error(f"Erro ao excluir planta: {e}", exc_info=True); ui.mostrar_erro(f"Erro: {e}")
