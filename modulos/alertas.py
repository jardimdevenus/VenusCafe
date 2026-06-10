# -*- coding: utf-8 -*-

"""
Venus Café - Módulo de Alertas Proativos
========================================

Este módulo contém a lógica para analisar os dados do sistema e gerar
alertas de gestão para o utilizador.
"""

import logging
from datetime import datetime, timedelta
from modulos import ui
from database import executar_query

def verificar_alertas_atividades(db_path: str) -> list:
    """
    Verifica as atividades registadas e gera alertas para tarefas atrasadas ou próximas.

    Args:
        db_path (str): Caminho para o arquivo do banco de dados.

    Returns:
        list: Uma lista de strings, onde cada string é uma mensagem de alerta.
              Retorna uma lista vazia se não houver alertas.
    """
    alertas = []
    try:
        # Query que busca a última data de aplicação para cada tipo de atividade
        # recorrente em cada talhão.
        query = """
        SELECT
            ta.nome,
            ta.intervalo_dias,
            ra.talhao_codigo,
            MAX(ra.data) as ultima_data
        FROM
            registros_atividades ra
        JOIN
            tipos_atividades ta ON ra.tipo_id = ta.id
        WHERE
            ta.intervalo_dias IS NOT NULL AND ta.intervalo_dias > 0
        GROUP BY
            ra.talhao_codigo, ta.id
        """
        
        ultimas_atividades = executar_query(db_path, query, fetch=True)
        if not ultimas_atividades:
            return [] # Sem atividades recorrentes, sem alertas.

        hoje = datetime.now().date()

        for nome_atividade, intervalo, talhao, ultima_data_str in ultimas_atividades:
            try:
                ultima_data = datetime.fromisoformat(ultima_data_str).date()
                dias_passados = (hoje - ultima_data).days
                
                # Se já passou do prazo
                if dias_passados > intervalo:
                    alerta = (f"Talhão {talhao}: '{nome_atividade}' está "
                              f"{ui.Cores.VERMELHO}ATRASADA{ui.Cores.AMARELO} "
                              f"({dias_passados - intervalo} dias).")
                    alertas.append(alerta)
                # Se está próximo do prazo (ex: 7 dias ou menos)
                elif intervalo - dias_passados <= 7:
                    dias_restantes = intervalo - dias_passados
                    alerta = (f"Talhão {talhao}: '{nome_atividade}' vence "
                              f"em {dias_restantes} dia(s).")
                    alertas.append(alerta)

            except (ValueError, TypeError):
                # Ignora se a data for inválida no banco de dados
                continue
        
        return alertas

    except Exception as e:
        logging.error(f"Erro ao verificar alertas de atividades: {e}", exc_info=True)
        # Retorna um alerta de erro para o usuário, mas não quebra o programa
        return ["Ocorreu um erro ao verificar os alertas de atividades."]

