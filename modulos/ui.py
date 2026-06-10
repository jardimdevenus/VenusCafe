# -*- coding: utf-8 -*-

"""
Venus Café - Módulo de Interface do Utilizador (UI)
"""

import os
import time
import sys
import termios
import tty
import logging
import re
from datetime import datetime

class Cores:
    """Namespace para códigos de cor ANSI para uso no terminal."""
    VERDE = '\033[92m'; AMARELO = '\033[93m'; VERMELHO = '\033[91m'
    MAGENTA = '\033[95m'; AZUL = '\033[94m'; CIANO = '\033[96m'
    BRANCO = '\033[97m'; CINZA = '\033[90m'; RESET = '\033[0m'

def mostrar_logo(titulo: str = "", contexto: list = None):
    """Exibe o logo do sistema, um caminho de navegação (breadcrumbs) e um título."""
    logo = f"""{Cores.MAGENTA}
░░░░░░░█░█░█▀▀░█▀█░█░█░█▀▀░░░█▀▀░█▀█░█▀▀░█▀▀░░░░░░
░░░░░░░▀▄▀░█▀▀░█░█░█░█░▀▀█░░░█░░░█▀█░█▀▀░█▀▀░░░░░░
░░░░░░░░▀░░▀▀▀░▀░▀░▀▀▀░▀▀▀░░░▀▀▀░▀░▀░▀░░░▀▀▀░░V1.0
    SISTEMA DE GESTÃO DE DADOS DA CAFEICULTURA
        Desenvolvido por Jardim de Vênus
    {Cores.RESET}"""
    print(logo)
    if contexto:
        caminho_str = f" {Cores.CINZA}›{Cores.RESET} ".join(contexto)
        print(f"{Cores.AMARELO}{caminho_str}{Cores.RESET}")
    if titulo:
        print(f"{Cores.VERDE}\n{'─' * 60}")
        print(f"{titulo.center(60)}")
        print(f"{'─' * 60}{Cores.RESET}")

def mostrar_tela_login():
    """Exibe uma tela de login estilizada com a logo e o nome do desenvolvedor."""
    limpar_tela()
    logo = f"""{Cores.MAGENTA}
     ██╗   ██╗███████╗███╗   ██╗██╗   ██╗███████╗
     ██║   ██║██╔════╝████╗  ██║██║   ██║██╔════╝
     ██║   ██║█████╗  ██╔██╗ ██║██║   ██║███████╗
     ╚██╗ ██╔╝██╔══╝  ██║╚██╗██║██║   ██║╚════██║
      ╚████╔╝ ███████╗██║ ╚████║╚██████╔╝███████║
       ╚═══╝  ╚══════╝╚═╝  ╚═══╝ ╚═════╝ ╚══════╝
     ██████╗ █████╗ ███████╗███████╗  ╔════╝╔════╝
    ██╔════╝██╔══██╗██╔════╝██╔════╝ ███████████═╗
    ██║     ███████║█████╗  █████╗    █████████ ╔╝
    ██║     ██╔══██║██╔══╝  ██╔══╝     ███████ ╔╝
    ╚██████╗██║  ██║██║     ███████╗    █████ ╔╝
     ╚═════╝╚═╝  ╚═╝╚═╝     ╚══════╝    ╚═════╝
    {Cores.RESET}"""
    print(logo)
    print(f"{Cores.CIANO}{'Desenvolvido por Jardim de Vênus'.center(60)}{Cores.RESET}")
    print("\n" * 2)

def limpar_tela():
    """Limpa a tela do terminal de forma multiplataforma."""
    os.system('cls' if os.name == 'nt' else 'clear')

def mostrar_erro(mensagem: str):
    """Exibe uma mensagem de erro padronizada."""
    print(f"\n{Cores.VERMELHO}[ERRO] {mensagem}{Cores.RESET}")
    time.sleep(2)

def mostrar_sucesso(mensagem: str):
    """Exibe uma mensagem de sucesso padronizada."""
    print(f"\n{Cores.VERDE}[SUCESSO] {mensagem}{Cores.RESET}")
    time.sleep(1.5)

def mostrar_alerta(mensagem: str):
    """Exibe uma mensagem de alerta padronizada."""
    print(f"\n{Cores.AMARELO}[ALERTA] {mensagem}{Cores.RESET}")
    time.sleep(1.5)

def obter_senha_mascarada(prompt: str = "Senha: ") -> str:
    """Captura a senha do utilizador de forma segura, exibindo asteriscos."""
    print(prompt, end='', flush=True)
    senha = ""
    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    try:
        tty.setraw(sys.stdin.fileno())
        while True:
            char = sys.stdin.read(1)
            if ord(char) in [10, 13]: break
            elif ord(char) == 127:
                if len(senha) > 0:
                    senha = senha[:-1]
                    sys.stdout.write('\b \b'); sys.stdout.flush()
            elif ord(char) == 3: raise KeyboardInterrupt
            else:
                senha += char
                sys.stdout.write('*'); sys.stdout.flush()
    except KeyboardInterrupt:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
        print("\nOperação cancelada.")
        sys.exit(0)
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
    print()
    return senha

def obter_numero_positivo(mensagem: str, tipo_dado: type = float, permitir_vazio: bool = False) -> float | int | None:
    """Solicita um número (float ou int) que deve ser positivo (maior ou igual a zero)."""
    while True:
        valor_str = input(mensagem).strip().replace(',', '.')
        if not valor_str and permitir_vazio: return None
        if not valor_str and not permitir_vazio:
            mostrar_erro("Este campo é obrigatório."); continue
        try:
            valor = tipo_dado(valor_str)
            if valor >= 0: return valor
            else: mostrar_erro("O valor não pode ser negativo.")
        except ValueError:
            mostrar_erro("Entrada inválida. Insira um número válido.")

def obter_data_valida(mensagem: str, default_hoje: bool = True) -> str | None:
    """Solicita uma data no formato DD/MM/AAAA e a valida."""
    prompt = f"{mensagem} (DD/MM/AAAA)"
    if default_hoje:
        hoje_br = datetime.now().strftime('%d/%m/%Y')
        prompt += f" [{hoje_br}]: "
    else:
        prompt += " (opcional): "
    while True:
        data_str = input(prompt).strip()
        if not data_str:
            return datetime.now().strftime('%Y-%m-%d') if default_hoje else None
        try:
            data_obj = datetime.strptime(data_str, '%d/%m/%Y')
            return data_obj.strftime('%Y-%m-%d')
        except ValueError:
            mostrar_erro("Formato de data inválido! Use DD/MM/AAAA.")

def converter_gms_para_gd(gms_str: str) -> float | None:
    """Tenta converter uma string de Graus, Minutos, Segundos (GMS) para Graus Decimais (GD)."""
    padrao = re.compile(
        r"^\s*(\d{1,3})\s*[°dD]?\s*(\d{1,2})\s*['mM]?\s*([\d\.]+)\s*[\"sS]?\s*([NSEWOLnsewol])\s*$", re.I
    )
    match = padrao.match(gms_str.strip())
    if not match: return None
    try:
        graus, minutos, segundos = float(match.group(1)), float(match.group(2)), float(match.group(3))
        direcao = match.group(4).upper()
        decimal = graus + (minutos / 60) + (segundos / 3600)
        if direcao in ['S', 'O', 'W']: return -decimal
        elif direcao in ['N', 'L', 'E']: return decimal
        return None
    except (ValueError, IndexError):
        return None

def obter_numero_decimal(mensagem: str, valor_atual=None) -> float | None:
    """Solicita e valida um número decimal (float), que pode ser positivo ou negativo."""
    prompt = f"{mensagem} [{valor_atual or 'N/D'}]: "
    while True:
        valor_str = input(prompt).strip().replace(',', '.')
        if not valor_str: return valor_atual
        try:
            return float(valor_str)
        except ValueError:
            mostrar_erro("Entrada inválida. Insira um número (ex: 25.5 ou -2.0).")

def obter_coordenada(mensagem: str, tipo: str, valor_atual=None) -> float | None:
    """Solicita e valida uma coordenada geográfica, aceitando o formato Decimal ou GMS."""
    limites = {'latitude': (-90.0, 90.0), 'longitude': (-180.0, 180.0)}
    limite = limites.get(tipo.lower())
    if limite is None:
        mostrar_erro(f"Erro de programação: tipo '{tipo}' inválido."); return None
    prompt = f"{mensagem} [{valor_atual or 'N/D'}]: "
    while True:
        valor_str = input(prompt).strip()
        if not valor_str: return valor_atual
        try:
            valor = float(valor_str.replace(',', '.'))
            if limite[0] <= valor <= limite[1]: return valor
            else: mostrar_erro(f"Valor inválido. Deve estar entre {limite[0]} e {limite[1]}.")
        except ValueError:
            valor_convertido = converter_gms_para_gd(valor_str)
            if valor_convertido is not None:
                if limite[0] <= valor_convertido <= limite[1]:
                    print(f"{Cores.CINZA}Valor convertido para decimal: {valor_convertido:.4f}{Cores.RESET}"); time.sleep(1)
                    return valor_convertido
                else: mostrar_erro(f"Valor GMS inválido. O resultado ({valor_convertido:.4f}) está fora dos limites.")
            else:
                mostrar_erro("Formato inválido. Use decimal (ex: -23.54) ou GMS (ex: 23 32 52 S).")

def selecionar_entidade(db_path: str, titulo: str, nome_tabela: str, colunas: list, where_clause: tuple = None) -> tuple | None:
    """Função genérica e inteligente para pesquisar, listar e selecionar uma entidade."""
    from database import executar_query
    try:
        termo_pesquisa = input(f"Pesquisar em {nome_tabela} por '{colunas[1]}' (Enter para listar todos): ").strip()
        colunas_str = ", ".join(colunas)
        query = f"SELECT {colunas_str} FROM {nome_tabela}"
        where_parts, params = [], []
        if where_clause:
            where_parts.append(where_clause[0]); params.extend(where_clause[1])
        if termo_pesquisa:
            where_parts.append(f"{colunas[1]} LIKE ?"); params.append(f"%{termo_pesquisa}%")
        if where_parts:
            query += " WHERE " + " AND ".join(where_parts)
        query += f" ORDER BY {colunas[1]}"
        todas_entidades = executar_query(db_path, query, tuple(params), fetch=True)
        if not todas_entidades:
            mostrar_alerta("Nenhum item encontrado com os critérios especificados."); return None
        pagina_atual = 1; itens_por_pagina = 15; total_itens = len(todas_entidades)
        total_paginas = max(1, (total_itens + itens_por_pagina - 1) // itens_por_pagina)
        while True:
            limpar_tela(); mostrar_logo(titulo)
            print(f"\n--- Exibindo Página {pagina_atual}/{total_paginas} ({total_itens} no total) ---")
            offset = (pagina_atual - 1) * itens_por_pagina
            entidades_pagina = todas_entidades[offset : offset + itens_por_pagina]
            for i, entidade in enumerate(entidades_pagina, 1):
                dados_exibicao = " - ".join(str(d) for d in entidade[1:])
                print(f" {i}. {dados_exibicao}")
            print("\n" + "─"*60); print("Digite o número para selecionar.")
            if total_paginas > 1: print("(P)róxima Página | (A)nterior", end=" | ")
            print("(C)ancelar")
            escolha_str = input(">>> ").strip().lower()
            if escolha_str == 'p' and pagina_atual < total_paginas: pagina_atual += 1; continue
            elif escolha_str == 'a' and pagina_atual > 1: pagina_atual -= 1; continue
            elif escolha_str == 'c': return None
            try:
                escolha_num = int(escolha_str)
                if 1 <= escolha_num <= len(entidades_pagina):
                    indice_real = offset + escolha_num - 1
                    return todas_entidades[indice_real]
                else: mostrar_erro("Número fora do intervalo da página atual.")
            except ValueError: mostrar_erro("Entrada inválida.")
    except Exception as e:
        logging.error(f"Erro ao selecionar entidade: {e}", exc_info=True)
        mostrar_erro(f"Ocorreu um erro inesperado: {e}"); return None

def selecionar_opcao_de_lista(titulo: str, opcoes: list, pode_cancelar: bool = True) -> str | None:
    """Exibe uma lista numerada de opções e retorna a string selecionada."""
    print(f"\n{titulo}")
    for i, opcao in enumerate(opcoes, 1): print(f" {i}. {opcao}")
    if pode_cancelar: print(" 0. Cancelar / Pular")
    while True:
        try:
            escolha_str = input("\n>>> Selecione: ").strip()
            if not escolha_str and pode_cancelar: return None
            escolha = int(escolha_str)
            if pode_cancelar and escolha == 0: return None
            if 1 <= escolha <= len(opcoes): return opcoes[escolha - 1]
            else: mostrar_erro("Seleção inválida.")
        except ValueError: mostrar_erro("Por favor, digite um número válido.")

def mostrar_tabela(cabecalhos: list, dados: list, larguras: list):
    """Exibe uma tabela formatada de forma genérica."""
    if len(cabecalhos) != len(larguras):
        mostrar_erro("Erro: Inconsistência entre cabeçalhos e larguras."); return
    header = " | ".join([f"{str(c):<{l}}" for c, l in zip(cabecalhos, larguras)])
    separator = "─┼─".join(['─' * w for w in larguras])
    print("\n" + header); print(separator)
    if not dados: return
    for i, linha in enumerate(dados):
        cor_linha = Cores.CIANO if i % 2 != 0 else Cores.RESET
        linha_formatada = []
        linha_completa = list(linha) + ['-'] * (len(larguras) - len(linha))
        for idx, item in enumerate(linha_completa):
            item_str = str(item or "N/D")
            if len(item_str) > larguras[idx]:
                item_str = item_str[:larguras[idx]-1] + '…'
            linha_formatada.append(f"{item_str:<{larguras[idx]}}")
        print(f"{cor_linha}{' | '.join(linha_formatada)}{Cores.RESET}")

def navegacao_paginada(db_path: str, contexto: list, titulo: str, nome_tabela: str, cabecalhos: list, larguras: list, colunas_db: list, join_clause: str = "", where_clause: tuple = None, group_by_clause: str = "", order_by_clause: str = None):
    """
    Função central para exibir listas longas com navegação por páginas e ordenação customizável.
    
    Args:
        order_by_clause (str, optional): A cláusula ORDER BY completa. 
                                         Ex: "data DESC" ou "nome ASC". 
                                         Se None, ordena pela segunda coluna.
    """
    from database import executar_query
    pagina_atual = 1
    itens_por_pagina = 15
    while True:
        limpar_tela()
        mostrar_logo(titulo, contexto=contexto)
        
        count_query_base = f"FROM {nome_tabela} {join_clause}"
        count_query = f"SELECT COUNT(*) {count_query_base}"
        if group_by_clause:
            count_query = f"SELECT COUNT(1) FROM (SELECT 1 {count_query_base}"
        
        params_total = []
        if where_clause:
            where_str = f" WHERE {where_clause[0]}"
            count_query += where_str
            params_total.extend(where_clause[1])
        if group_by_clause:
            count_query += f" GROUP BY {group_by_clause})"
        
        total_itens_result = executar_query(db_path, count_query, tuple(params_total), fetch=True)
        total_itens = total_itens_result[0][0] if total_itens_result else 0
        
        if total_itens == 0:
            mostrar_alerta("Nenhum item encontrado."); input("Pressione Enter..."); return

        total_paginas = max(1, (total_itens + itens_por_pagina - 1) // itens_por_pagina)
        offset = (pagina_atual - 1) * itens_por_pagina
        
        colunas_str = ", ".join(colunas_db)
        query_dados = f"SELECT {colunas_str} FROM {nome_tabela} {join_clause}"
        params_dados = []
        if where_clause:
            query_dados += f" WHERE {where_clause[0]}"; params_dados.extend(where_clause[1])
        if group_by_clause:
            query_dados += f" GROUP BY {group_by_clause}"
        if order_by_clause:
            query_dados += f" ORDER BY {order_by_clause}"
        else:
            # Comportamento padrão: ordenar pela segunda coluna
            query_dados += f" ORDER BY {colunas_db[1]}"

        query_dados += f" LIMIT ? OFFSET ?"
        params_dados.extend([itens_por_pagina, offset])
        
        dados_pagina = executar_query(db_path, query_dados, tuple(params_dados), fetch=True)
        
        print(f"\n--- Exibindo Página {pagina_atual}/{total_paginas} ({total_itens} no total) ---")
        mostrar_tabela(cabecalhos, dados_pagina, larguras)
        
        print("\n(P)róxima Página | (A)nterior | (S)air")
        comando = input(">>> ").strip().lower()

        if comando == 'p' and pagina_atual < total_paginas: pagina_atual += 1
        elif comando == 'a' and pagina_atual > 1: pagina_atual -= 1
        elif comando == 's': break

def mostrar_tela_sobre():
    """
    Exibe uma tela "Sobre" com informações sobre o projeto Venus Café,
    a filosofia open source e um apelo para doações.
    """
    contexto = ["Sobre"]
    limpar_tela()
    mostrar_logo("Sobre o Venus Café", contexto=contexto)

    texto = f"""
    {Cores.BRANCO}O {Cores.MAGENTA}Venus Cafe{Cores.BRANCO} é um sistema de gestão de dados da cafeicultura, de código aberto (open source),
    desenvolvido por Sérgio Melo (Analista de sistemas e cafeicultor), idealizador do projeto {Cores.VERDE}Jardim de Vênus{Cores.BRANCO},
    projeto que atua no processo de restauração ecológica e educação ambiental.
    
    A nossa missão é fornecer uma ferramenta poderosa, gratuita e acessível para
    pequenos e médios cafeicultores, ajudando a organizar a gestão da lavoura,
    a tomar melhores decisões e a melhorar a qualidade do café.

    {Cores.AMARELO}A Importância do Código Aberto (Open Source){Cores.RESET}
    
    Por ser um projeto de código aberto, o Venus Cafe garante ao agricultor ou agricultora,
    total liberdade e controle sobre os seus dados e as suas ferramentas.
    
     - {Cores.VERDE}Gratuito e livre:{Cores.RESET} Pode usar, modificar e distribuir este programa livremente.
     - {Cores.VERDE}Transparência Total:{Cores.RESET} O código-fonte está disponível para auditoria.
     - {Cores.VERDE}Sem Dependência:{Cores.RESET} Você nunca ficará "preso" a uma empresa ou a mensalidades.
     - {Cores.VERDE}Comunidade:{Cores.RESET} Acreditamos no poder da colaboração para evoluir a ferramenta.

    {Cores.AMARELO}Apoie o Projeto!{Cores.RESET}

    Se o Venus Café está sendo útil para a gestão de sua lavoura, por favor, considere
    apoiar o nosso desenvolvimento contínuo. A sua contribuição ajuda a
    financiar o tempo e os recursos necessários para adicionar novos módulos,
    corrigir bugs e manter o sistema atualizado, além de também colaborar com a restauração ecológica do bioma Cerrado.

    {Cores.CIANO}Chave PIX para doações:{Cores.RESET} (38999092924)

    CONTATO: (38) 99909 - 2924  EMAIL: jardimdevenus@tech-center.com   

    Agradecemos imensamente o seu apoio e o seu feedback!
    """
    
    
    print(texto)
    input("\n\nPressione Enter para voltar ao menu...")

def mostrar_manual_usuario(contexto_pai: list):
    """
    Exibe um manual do utilizador interativo, dividido por secções.
    """
    contexto = [contexto_pai] + ["Manual do Usuário"]
  
    # Textos de ajuda para cada seção
    textos_ajuda = {
        "1": f"""
{Cores.AMARELO}--- Operações de Campo ---{Cores.RESET}
Esta seção tem seu foco no registro das tarefas diárias da lavoura.

{Cores.CIANO}Registrar Atividade Agrícola:{Cores.RESET}
Permite registrar uma atividade (ex: Adubação, Colheita). O sistema irá
guiá-lo para selecionar o tipo de atividade, o alvo (Talhão, Linha ou
uma planta específica), os insumos utilizados (com custos), e o colaborador
responsável. É o coração do diário de campo digital.

{Cores.CIANO}Listar Atividades Registradas:{Cores.RESET}
Aqui pode consultar o histórico de todas as atividades. O sistema permite
filtrar por Talhão ou por Tipo de Atividade para encontrar rapidamente a
informação que procura.
""",
        "2": f"""
{Cores.AMARELO}--- Cadastros de Base ---{Cores.RESET}
Esta seção contém os "alicerces" da sua fazenda. São os dados que
você registra uma vez e raramente altera.

{Cores.CIANO}Gestão de Talhões, Linhas e Plantas:{Cores.RESET}
A estrutura principal da sua lavoura. Primeiro, crie os Talhões (as áreas
geográficas). Depois, dentro de cada talhão, crie as Linhas de café. Ao
criar uma linha, o sistema irá criar automaticamente os registos para
cada planta individualmente.

{Cores.CIANO}Gestão de Cultivares:{Cores.RESET}
O seu catálogo de cultivares de café. Registre aqui as características
agronômicas de cada cultivar (ex: Catuaí, Mundo Novo) para referência
e para as associar às suas plantas.

{Cores.CIANO}Gestão de Insumos:{Cores.RESET}
O seu inventário de produtos. Registe aqui todos os fertilizantes,
defensivos, etc., que utiliza na fazenda, com a sua unidade de medida
padrão (kg, L, etc.).
""",
        "3": f"""
{Cores.AMARELO}--- Ferramentas Avançadas ---{Cores.RESET}
Esta secção contém os módulos de análise e dados de precisão.

{Cores.CIANO}Clima & Ambiente:{Cores.RESET}
Registe os dados diários da sua estação meteorológica (chuva, temperaturas).
Se se esquecer de um dia, use a opção de Sincronização via API para que o
sistema busque os dados em falta na internet (requer Latitude/Longitude
no Perfil da Propriedade e chaves de API nas Configurações).

{Cores.CIANO}Análises (Solo/Folha):{Cores.RESET}
Registe aqui os resultados dos seus laudos de laboratório. O sistema permite
inserir os dados gerais da análise (data, talhão) e depois cada resultado
individual (ex: pH, Fósforo, Potássio), criando um histórico digital
completo das suas análises.

{Cores.CIANO}Relatórios & Análises:{Cores.RESET}
Transforme os seus dados em conhecimento. Gere relatórios financeiros
(ex: Custo por Talhão) e operacionais (ex: Atividades por Colaborador)
para ajudar na tomada de decisão.
"""
    }

    while True:
        limpar_tela()
        mostrar_logo("Manual do Usuário", contexto=contexto)
        print("\nSobre qual secção do sistema você gostaria de ler?")
        print("\n[1] Operações de Campo")
        print("[2] Cadastros de Base")
        print("[3] Ferramentas Avançadas")
        print("[0] Voltar ao Menu Principal")

        topico = input("\n>>> Selecione o tópico: ").strip()

        if topico in textos_ajuda:
            limpar_tela()
            mostrar_logo("Manual do Usuário", contexto=contexto)
            print(textos_ajuda[topico])
            input("\nPressione Enter para voltar ao menu de ajuda...")
        elif topico == '0':
            return
        else:
            mostrar_erro("Tópico inválido.")
