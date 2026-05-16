import datetime
from core.browser import browse_execute
from core.connections import login_no_mapia, entrar_em_aplicacao
from core.collections import coletar_marcos
from core.helpers import limpar_dados_marcos, salvar_em_planilha_excel
from gui.dialogs import pedir_mes_ano_padrao, selecionar_mes_ano, selecionar_esteiras

def executar_coleta_marcos(root):
    """
    Orquestra a coleta de marcos: realiza login, configura parâmetros de data (mês/ano) e
    seleção de esteiras/estações via interface, executa a raspagem e salva o Excel.
    """
    def rotina(contexto):
        awsPagina = login_no_mapia(contexto)
        mapiaAplicacao = entrar_em_aplicacao(awsPagina, "gpo")
        
        mapiaAplicacao.goto("https://gpo.mapia.ai/marcos", timeout=60000)
        mapiaAplicacao.locator("#mes").wait_for(state="attached", timeout=10000)

        res_padrao = pedir_mes_ano_padrao(root, mapiaAplicacao)
        if res_padrao.get('cancelado'):
            print("Coleta de marcos cancelada pelo usuário (Mês/Ano).")
            return
            
        padrao = res_padrao.get('padrao', False)

        if padrao:
            hoje = datetime.datetime.now()
            primeiro_dia_mes_atual = hoje.replace(day=1)
            mes_passado = primeiro_dia_mes_atual - datetime.timedelta(days=1)
            valor_mes_selecionado = str(mes_passado.month)
            valor_ano_selecionado = str(mes_passado.year)
        else:
            meses_opcoes = mapiaAplicacao.locator("#mes option").all()
            anos_opcoes = mapiaAplicacao.locator("#ano option").all()
            
            dict_meses = {m.inner_text().strip(): m.get_attribute("value") for m in meses_opcoes if m.get_attribute("value")}
            lista_anos = [a.get_attribute("value") for a in anos_opcoes if a.get_attribute("value")]
            
            res_mes_ano = selecionar_mes_ano(root, mapiaAplicacao, dict_meses, lista_anos)
            if res_mes_ano.get('cancelado'):
                print("Coleta de marcos cancelada pelo usuário (Selecionar Mês/Ano).")
                return
                
            valor_mes_selecionado = res_mes_ano['mes_val']
            valor_ano_selecionado = res_mes_ano['ano_val']

        esteirasEstacoes_opcoes = mapiaAplicacao.locator("#milestones option").all()
        lista_opcoes = []
        
        nomes_esteiras = {}
        nomes_estacoes = {}

        for opcao in esteirasEstacoes_opcoes:
            texto = opcao.inner_text()
            valor = opcao.get_attribute("value")

            if texto == "Todos" or "-" not in valor:
                continue

            esteira, estacao = valor.split("-", 1)
            if "-" in texto:
                nome_esteira, nome_estacao = [x.strip() for x in texto.split("-", 1)]
            else:
                nome_esteira, nome_estacao = esteira, estacao
                
            nomes_esteiras.setdefault(esteira, nome_esteira)
            nomes_estacoes.setdefault(estacao, nome_estacao)

            lista_opcoes.append({
                'esteira': esteira,
                'nome_esteira': nome_esteira,
                'estacao': estacao,
                'nome_estacao': nome_estacao
            })
            
        res_esteiras = selecionar_esteiras(root, mapiaAplicacao, lista_opcoes)
        if res_esteiras.get('cancelado'):
            print("Coleta de marcos cancelada pelo usuário (Selecionar Esteiras).")
            return
            
        selecao_esteiras_dict = res_esteiras['selecao']
        
        dados = coletar_marcos(mapiaAplicacao, valor_mes_selecionado, valor_ano_selecionado, selecao_esteiras_dict, nomes_esteiras, nomes_estacoes, callback=root.update_progress)
        
        if dados:
            root.update_progress(100, 100, "Finalizando coleta e gerando planilha...")
            df = limpar_dados_marcos(dados)
            sufixo_marcos = f"{valor_mes_selecionado}_{valor_ano_selecionado}"
            salvar_em_planilha_excel(df, "Coleta_Marcos", sufixo_data=sufixo_marcos)

    browse_execute(activate=rotina)
