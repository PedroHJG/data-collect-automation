import datetime
import exceptions
from core.logger import get_logger

logger = get_logger()

def coletar_operadores(mapiaAplicacao, data_alvo_formatada, callback=None):
    """
    Navega pelo painel de desempenho e coleta as métricas de tempo e atividades realizadas por todos os operadores ativos.
    Retorna uma lista de dicionários com os registros extraídos baseados na data alvo.
    """
    try:
        mapiaAplicacao.goto("https://gpo.mapia.ai/analises/desempenho", timeout=60000)
        mapiaAplicacao.locator("#date_type").select_option("calendar")
        mesAtual = str(datetime.datetime.now().month)
        anoAtual = str(datetime.datetime.now().year)
        mapiaAplicacao.locator("#mes").select_option(mesAtual)
        mapiaAplicacao.locator("#ano").select_option(anoAtual)
    except Exception as e:
        logger.error(f"Dev Error: Falha ao carregar a tela de Desempenho: {e}", exc_info=True)
        raise exceptions.DataCollectionException("Não foi possível carregar a página de Desempenho. Tente novamente.")

    try:
        operador_select = mapiaAplicacao.locator("#operador")
        operador_select.wait_for()
        operadores_raw = operador_select.locator("option").all()
        operadores = []

        for op in operadores_raw:
            valor = op.get_attribute("value")
            classe = op.get_attribute("class")
            # Ignora inativos e value 0
            if valor != "0" and classe != "inactive":
                operadores.append(valor)
    except Exception as e:
        logger.error(f"Dev Error: Falha ao coletar lista de operadores: {e}", exc_info=True)
        raise exceptions.DataCollectionException("Não foi possível carregar a lista de operadores.")

    mesColeta = data_alvo_formatada.split("-")[1]
    anoColeta = data_alvo_formatada.split("-")[2]
    todosDadosMapiaOperadorFiltrado = []

    colunasMapiaOperador = [
        "Data",
        "Operador",
        "Caso",
        "Cliente",
        "Estação",
        "Esteira",
        "Tempo_trabalhado_min"
    ]

    # ===============================
    # Loopar sobre operadores
    total_ops = len(operadores)
    for idx, valor in enumerate(operadores):
        if callback:
            callback(idx + 1, total_ops, f"Coletando operador {idx + 1} de {total_ops}...")
            
        # Seleciona operador (dispara reload)
        mapiaAplicacao.locator("#operador").select_option(valor)
        # carrega o primeiro operador como URL pois antes estava pulando.
        if operadores.index(valor) == 0:
            mapiaAplicacao.goto(
                f"https://gpo.mapia.ai/analises/desempenho?operador={valor}&mes={mesColeta}&ano={anoColeta}&status=1&date_type=calendar")
        # Espera tabela carregar
        tabela = mapiaAplicacao.locator("table#tabela_estacoes_trabalhadas_por_dia")
        try:
            tabela.wait_for(state="visible", timeout=10000)  # espera até 10s
        except:
            # Se não carregar, pula operador
            continue

        # Filtra linhas pela data
        linhas_data = tabela.locator(f"tr:has-text('{data_alvo_formatada}')")
        if linhas_data.count() == 0:
            continue  # pula se não houver dados da data alvo

        # Coleta dados
        linhas_texto = linhas_data.all_inner_texts()
        for linha_texto in linhas_texto:
            celulas = linha_texto.split("\t")
            if len(celulas) == len(colunasMapiaOperador):
                registroMapiaOperador = dict(zip(colunasMapiaOperador, celulas))
                todosDadosMapiaOperadorFiltrado.append(registroMapiaOperador)

    return todosDadosMapiaOperadorFiltrado


def coletar_marcos(mapiaAplicacao, valor_mes_selecionado, valor_ano_selecionado, values_esteiras_estacoes_selecionadas, nomes_esteiras, nomes_estacoes, callback=None):
    """
    Percorre a tela de Marcos da aplicação para as esteiras e estações selecionadas, iterando sobre as paginações e coletando as obrigações e status de conclusão no mês/ano específicos.
    Retorna uma lista de dicionários com os registros extraídos.
    """
    colunas_marcos = [
        "Caso", "Empresa", "Meta", "Alcançado", "Data Alcan",
        "Obrigações Totais", "Obrigações Produzidas",
        "Obrigações Detalhadas", "Esteira", "Estação"
    ]

    lista_registros_marcos = []
    
    total_items = sum(len(v) for v in values_esteiras_estacoes_selecionadas.values())
    contador = 0

    print(f"Iniciando extração de {total_items} estações...")

    for esteira, estacoes in values_esteiras_estacoes_selecionadas.items():
        for estacao in estacoes:
            contador += 1
            nome_e = nomes_estacoes.get(estacao, estacao)
            print(f"[ {contador}/{total_items} ] Coletando: {nome_e}")
            if callback:
                callback(contador, total_items, f"Coletando estação: {nome_e} ({contador}/{total_items})")

            try:
                mapiaAplicacao.goto(
                    f"https://gpo.mapia.ai/marcos?"
                    f"mes={valor_mes_selecionado}&ano={valor_ano_selecionado}"
                    f"&milestones={esteira}-{estacao}",
                    timeout=60000
                )

                try:
                    mapiaAplicacao.locator("#total").click(timeout=5000)
                except:
                    pass

                mapiaAplicacao.locator("#datatable_marco_length select").select_option("100")

                tbody = mapiaAplicacao.locator("#datatable_marco tbody")
                botao_next = mapiaAplicacao.locator("#datatable_marco_next")

                while True:
                    tbody.locator("tr").first.wait_for(state="visible", timeout=5000)
                    linhas = tbody.locator("tr").all_inner_texts()

                    for linha in linhas:
                        if "Nenhum registro" in linha: continue

                        dados = linha.split("\t") + [nomes_esteiras.get(esteira), nomes_estacoes.get(estacao)]
                        if len(dados) == len(colunas_marcos):
                            lista_registros_marcos.append(dict(zip(colunas_marcos, dados)))

                    if "disabled" in (botao_next.get_attribute("class") or ""):
                        break
                    botao_next.click()
                    mapiaAplicacao.wait_for_timeout(500)

            except Exception as e:
                logger.error(f"Dev Error: Erro ao coletar marco da estação {nome_e}: {e}", exc_info=True)
                print(f"Erro na estação {nome_e}. Pulando...")
                continue
                
    return lista_registros_marcos