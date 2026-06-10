# -*- coding: utf-8 -*-

"""
Venus Café - Módulo de Banco de Dados
=====================================

Este módulo centraliza todas as operações relacionadas ao banco de dados SQLite,
incluindo a criação da estrutura (schema), migrações, backups e a execução
de consultas.
"""

import os
import re
import sqlite3
import shutil
import logging
import hashlib
import time
from datetime import datetime
from modulos import ui

def criar_banco_dados(db_path: str) -> bool:
    """
    Cria e/ou migra o schema do banco de dados para a versão mais recente.
    """
    conn = None
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("PRAGMA foreign_keys = ON;")

        # --- Definição do Schema Completo ---
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS usuarios (id INTEGER PRIMARY KEY AUTOINCREMENT, usuario TEXT NOT NULL UNIQUE, hash_senha TEXT NOT NULL, sal TEXT NOT NULL, nome_completo TEXT, email TEXT, perfil TEXT )
        ''')
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS perfil_agricultor (id INTEGER PRIMARY KEY AUTOINCREMENT, nome TEXT, propriedade TEXT, endereco TEXT, telefone TEXT, email TEXT, area_total REAL, latitude REAL, longitude REAL, altitude_min REAL, altitude_max REAL)
        ''')
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS cultivares (codigo TEXT PRIMARY KEY, nome TEXT NOT NULL UNIQUE, origem TEXT, mantenedor TEXT, ano_registro INTEGER, consideracoes TEXT, porte TEXT, diametro_copa TEXT, vigor TEXT, epoca_maturacao TEXT, produtividade TEXT, cor_fruto_maduro TEXT, tamanho_grao TEXT, cor_folhas_jovens TEXT, qualidade_bebida TEXT, resistencia_ferrugem TEXT, resistencia_nematoide TEXT, resistencia_outras TEXT )
        ''')
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS talhoes (codigo TEXT PRIMARY KEY, nome TEXT NOT NULL, latitude REAL, longitude REAL, espacamento_linha REAL NOT NULL, consideracoes TEXT, cultivar_codigo_padrao TEXT, altitude_media REAL, FOREIGN KEY(cultivar_codigo_padrao) REFERENCES cultivares(codigo) )
        ''')
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS linhas (id INTEGER PRIMARY KEY AUTOINCREMENT, codigo TEXT NOT NULL, talhao_codigo TEXT NOT NULL, numero INTEGER NOT NULL, quantidade_plantas INTEGER, cultivar_codigo TEXT, espacamento_planta REAL, FOREIGN KEY(talhao_codigo) REFERENCES talhoes(codigo) ON DELETE CASCADE, FOREIGN KEY(cultivar_codigo) REFERENCES cultivares(codigo), UNIQUE(talhao_codigo, codigo))
        ''')
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS plantas (id INTEGER PRIMARY KEY AUTOINCREMENT, codigo TEXT, linha_id INTEGER NOT NULL, numero_na_linha INTEGER NOT NULL, cultivar_codigo TEXT, data_plantio TEXT, substituta BOOLEAN DEFAULT 0, observacoes TEXT, status TEXT DEFAULT 'ativa', FOREIGN KEY(linha_id) REFERENCES linhas(id) ON DELETE CASCADE, FOREIGN KEY(cultivar_codigo) REFERENCES cultivares(codigo), UNIQUE(linha_id, numero_na_linha))
        ''')
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS tipos_atividades (
            id INTEGER PRIMARY KEY AUTOINCREMENT, 
            nome TEXT NOT NULL UNIQUE, 
            descricao TEXT, 
            categoria TEXT, 
            recorrente BOOLEAN DEFAULT 0,
            intervalo_dias INTEGER 
        )
        ''')
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS insumos (id INTEGER PRIMARY KEY AUTOINCREMENT, nome TEXT NOT NULL UNIQUE, categoria TEXT, unidade_medida TEXT NOT NULL )
        ''')
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS colaboradores (id INTEGER PRIMARY KEY AUTOINCREMENT, nome_completo TEXT NOT NULL UNIQUE, funcao TEXT, status TEXT NOT NULL DEFAULT 'ativo' )
        ''')
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS registros_atividades (id INTEGER PRIMARY KEY AUTOINCREMENT, tipo_id INTEGER NOT NULL, talhao_codigo TEXT, linha_id INTEGER, planta_id INTEGER, data TEXT NOT NULL, observacoes TEXT, detalhes TEXT, insumo_id INTEGER, quantidade_insumo REAL, custo_total REAL, colaborador_id INTEGER, FOREIGN KEY(tipo_id) REFERENCES tipos_atividades(id), FOREIGN KEY(talhao_codigo) REFERENCES talhoes(codigo), FOREIGN KEY(linha_id) REFERENCES linhas(id), FOREIGN KEY(planta_id) REFERENCES plantas(id), FOREIGN KEY(insumo_id) REFERENCES insumos(id), FOREIGN KEY(colaborador_id) REFERENCES colaboradores(id))
        ''')
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS registros_climaticos (id INTEGER PRIMARY KEY AUTOINCREMENT, data_leitura TEXT NOT NULL UNIQUE, precipitacao_mm REAL, temperatura_min_c REAL, temperatura_max_c REAL, umidade_relativa_percent REAL, fonte TEXT NOT NULL)
        ''')
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS configuracoes (chave TEXT PRIMARY KEY, valor TEXT)
        ''')
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS analises (id INTEGER PRIMARY KEY AUTOINCREMENT, tipo_analise TEXT NOT NULL, sub_tipo TEXT, data_coleta TEXT NOT NULL, talhao_codigo_associado TEXT, laboratorio TEXT, recomendacoes TEXT, FOREIGN KEY(talhao_codigo_associado) REFERENCES talhoes(codigo))
        ''')
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS resultados_analise (id INTEGER PRIMARY KEY AUTOINCREMENT, analise_id INTEGER NOT NULL, parametro TEXT NOT NULL, valor REAL NOT NULL, unidade_medida TEXT, interpretacao TEXT, FOREIGN KEY(analise_id) REFERENCES analises(id) ON DELETE CASCADE)
        ''')
        cursor.execute('''
        CREATE UNIQUE INDEX IF NOT EXISTS idx_posicao_unica_ativa ON plantas(linha_id, numero_na_linha) WHERE status = 'ativa';
        ''')
        conn.commit()

        # --- Lógica de Migração ---
        cursor.execute("PRAGMA table_info(tipos_atividades)")
        colunas_tipos = [col[1] for col in cursor.fetchall()]
        if 'intervalo_dias' not in colunas_tipos or 'unidade_medida' in colunas_tipos:
            logging.info("MIGRANDO SCHEMA: Atualizando a tabela 'tipos_atividades'.")
            ui.mostrar_alerta("A atualizar estrutura da tabela de Tipos de Atividade...")
            
            cursor.execute("PRAGMA foreign_keys=off;")
            cursor.execute("ALTER TABLE tipos_atividades RENAME TO tipos_atividades_old;")
            cursor.execute('''
                CREATE TABLE tipos_atividades (
                    id INTEGER PRIMARY KEY AUTOINCREMENT, nome TEXT NOT NULL UNIQUE, 
                    descricao TEXT, categoria TEXT, recorrente BOOLEAN DEFAULT 0, intervalo_dias INTEGER
                )''')
                
            cursor.execute("INSERT INTO tipos_atividades (id, nome, descricao, categoria, recorrente) SELECT id, nome, descricao, categoria, recorrente FROM tipos_atividades_old;")
            cursor.execute("DROP TABLE tipos_atividades_old;")
            cursor.execute("PRAGMA foreign_keys=on;")
            conn.commit()
            ui.mostrar_sucesso("Estrutura atualizada com sucesso!")
        
        # --- Criação do Utilizador Admin Padrão ---
        cursor.execute("SELECT COUNT(*) FROM usuarios")
        if cursor.fetchone()[0] == 0:
            sal = os.urandom(16)
            senha = "admin123"
            hash_senha = hashlib.pbkdf2_hmac('sha256', senha.encode(), sal, 100000).hex()
            cursor.execute("INSERT INTO usuarios (usuario, hash_senha, sal, nome_completo, perfil) VALUES (?, ?, ?, ?, ?)", ('admin', hash_senha, sal.hex(), 'Administrador', 'admin'))
            conn.commit()
        return True

    except Exception as e:
        logging.critical(f"Erro CRÍTICO ao criar/migrar banco de dados: {e}", exc_info=True)
        print(f"[ERRO] Falha crítica no banco de dados: {e}")
        return False
    finally:
        if conn:
            conn.close()

def fazer_backup(db_path: str, backup_dir: str) -> bool:
    """Cria uma cópia de segurança do arquivo do banco de dados."""
    try:
        if not os.path.exists(db_path): return True
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = os.path.join(backup_dir, f"backup_{timestamp}.db")
        shutil.copy2(db_path, backup_file)
        logging.info(f"Backup criado com sucesso: {backup_file}")
        return True
    except Exception as e:
        ui.mostrar_erro(f"Backup falhou: {str(e)}"); return False

def gerar_proximo_codigo_talhao(db_path: str) -> str:
    """Gera o próximo código sequencial para um talhão."""
    try:
        query = "SELECT MAX(CAST(SUBSTR(codigo, 2) AS INTEGER)) FROM talhoes WHERE codigo LIKE 'T%'"
        resultado = executar_query(db_path, query, fetch=True)
        ultimo_num = resultado[0][0] if resultado and resultado[0][0] is not None else 0
        return f"T{ultimo_num + 1}"
    except Exception as e:
        logging.error(f"Erro ao gerar código de talhão: {e}"); return f"T{int(time.time())}"

def gerar_proximo_codigo_cultivar(db_path: str) -> str:
    """Gera o próximo código sequencial para um cultivar."""
    try:
        query = "SELECT MAX(CAST(SUBSTR(codigo, 2) AS INTEGER)) FROM cultivares WHERE codigo LIKE 'C%'"
        resultado = executar_query(db_path, query, fetch=True)
        ultimo_num = resultado[0][0] if resultado and resultado[0][0] is not None else 0
        return f"C{ultimo_num + 1}"
    except Exception as e:
        logging.error(f"Erro ao gerar código de cultivar: {e}"); return f"C{int(time.time())}"

def gerar_proximo_codigo_planta_no_talhao(db_path: str, talhao_codigo: str) -> str:
    """Gera o próximo código sequencial para uma planta dentro de um talhão (ex: P1, P2, ...)."""
    try:
        query = "SELECT p.codigo FROM plantas p JOIN linhas l ON p.linha_id = l.id WHERE l.talhao_codigo = ? AND p.codigo LIKE 'P%'"
        resultado = executar_query(db_path, query, (talhao_codigo,), fetch=True)
        maior_numero = 0
        if resultado:
            # O ciclo 'for' começa neste nível de indentação
            for r in resultado:
                # Tudo o que está dentro do 'for' deve ter um nível a mais, como abaixo
                numeros = re.findall(r'^P(\d+)', r[0])
                if numeros:
                    numero = int(numeros[0])
                    if numero > maior_numero:
                        maior_numero = numero
        return f"P{maior_numero + 1}"
    except Exception as e:
        logging.error(f"Erro ao gerar código de planta para {talhao_codigo}: {e}"); return f"P{int(time.time())}"

def executar_query(db_path: str, query: str, params: tuple = (), fetch: bool = False):
    """Função central para executar todas as consultas SQL no banco de dados."""
    conn = None
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("PRAGMA foreign_keys = ON;")
        cursor.execute(query, params)
        if fetch:
            return cursor.fetchall()
        else:
            conn.commit()
            return True
    except sqlite3.Error as e:
        logging.error(f"Erro SQL na query '{query[:50]}...': {e}")
        if conn: conn.rollback()
        return False
    finally:
        if conn: conn.close()
