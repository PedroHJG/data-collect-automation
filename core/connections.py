import exceptions
from .auth import buscar_credenciais
from core.logger import get_logger

logger = get_logger()

def login_no_mapia(contexto):
    """
    Realiza a autenticação na plataforma AWS usando as credenciais cadastradas e redireciona para o portal de aplicações do Mapia.
    Retorna a instância da página (awsPagina) logada.
    """
    credenciais = buscar_credenciais()
    usuario = credenciais.get("usuario")
    senha = credenciais.get("senha")
    
    mapiaPagina = contexto.new_page()
    mapiaPagina.goto('https://www.mapia.ai/')
    mapiaBtnCliente = mapiaPagina.get_by_role("link", name="Área do Cliente").nth(1)
    
    with contexto.expect_page() as mapia_to_aws:
        mapiaBtnCliente.click()
        
    awsPagina = mapia_to_aws.value
    awsPagina.wait_for_load_state("domcontentloaded")

    usuario_input = awsPagina.locator("input#awsui-input-0")
    usuario_input.fill(usuario)
    awsPagina.locator("button:has-text('Próximo')").click()

    senha_input = awsPagina.locator("input[type='password']")
    senha_input.fill(senha)
    
    try:
        awsPagina.locator("button:has-text('Sign in'), button:has-text('Fazer login')").click()
        awsPagina.wait_for_load_state("networkidle")
    except Exception as e:
        logger.error(f"Dev Error: Falha no login AWS: {e}", exc_info=True)
        raise exceptions.ConnectionException("Erro ao tentar fazer login. O botão de login pode ter mudado ou a rede caiu.")

    return awsPagina

def entrar_em_aplicacao(awsPagina, aplicacao: str):
    """
    Navega a partir do portal da AWS para uma aplicação específica do Mapia (ex: GPO, EDP).
    Aguarda a conclusão dos redirecionamentos de SSO e retorna a nova página carregada.
    """
    aplicacoes = {
        "gpo": "GPO - Produção e Operação",
        "edp": "EDP - Esteira de Produção",
        "pro": "Esteira de Projetos"
    }

    app_key = aplicacao.lower()

    if app_key not in aplicacoes:
        logger.warning(f"Usuário tentou acessar aplicação inválida: {aplicacao}")
        opcoes = ", ".join(aplicacoes.keys())
        raise exceptions.ConnectionException(f"Não existe essa aplicação: {aplicacao}\nInforme alguma destas: {opcoes}")

    nome_completo_app = aplicacoes[app_key]

    try:
        awsPagina.get_by_role("tab", name="Aplicações").click()
        with awsPagina.context.expect_page() as mapia_app_page:
            awsPagina.get_by_role("link", name=nome_completo_app).click()
            
        nova_pagina = mapia_app_page.value
        nova_pagina.wait_for_url("**/*.mapia.ai/**", timeout=60000)
        nova_pagina.wait_for_load_state("domcontentloaded")
        return nova_pagina
    except Exception as e:
        logger.error(f"Dev Error: Falha ao redirecionar para {nome_completo_app}: {e}", exc_info=True)
        raise exceptions.ConnectionException(f"Ocorreu um erro ou demora excessiva ao carregar o aplicativo {nome_completo_app}.")
