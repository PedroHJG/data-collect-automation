from core.browser import browse_execute
from core.connections import login_no_mapia, entrar_em_aplicacao
from core.collections import coletar_operadores
from core.helpers import limpar_dados_operadores, atualizar_planilha_produtividade
from gui.dialogs import pedir_data_operadores
import datetime
from core.auth import buscar_credenciais

def executar_atualizacao_planilha(root):
    """
    Orquestra o fluxo de atualização da planilha de produtividade.
    Realiza o login, solicita ao usuário a data de pesquisa, coleta os dados do Mapia de operadores,
    limpa o resultado e atualiza a planilha Produtividade cp1.xlsx de forma incremental.
    """
    def rotina(contexto):
        credenciais = buscar_credenciais()
        caminho_planilha = credenciais.get("caminho_planilha")
        
        awsPagina = login_no_mapia(contexto)
        mapiaAplicacao = entrar_em_aplicacao(awsPagina, "gpo")
        
        res = pedir_data_operadores(root, mapiaAplicacao)
        if not res.get('confirmado'):
            print("Atualização cancelada pelo usuário.")
            return

        if res.get('tipo') == 'padrao':
            hoje = datetime.datetime.today()
            weekday = hoje.weekday()
            dias_sub = 3 if weekday == 0 else (2 if weekday == 6 else 1)
            data_alvo = hoje - datetime.timedelta(days=dias_sub)
            data_alvo_formatada = data_alvo.strftime("%d-%m-%Y")
        else:
            data_alvo_formatada = res.get('data_alvo')
        
        dados = coletar_operadores(mapiaAplicacao, data_alvo_formatada, callback=root.update_progress)
        
        if dados:
            root.update_progress(100, 100, "Finalizando coleta e atualizando planilha...")
            df = limpar_dados_operadores(dados)
            atualizar_planilha_produtividade(df, caminho_planilha)

    browse_execute(activate=rotina)
