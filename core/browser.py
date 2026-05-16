from playwright.sync_api import sync_playwright

def browse_execute(activate, headless=True):
    """
    Inicializa o motor do Playwright e gerencia o ciclo de vida do navegador.
    Recebe uma função de automação 'activate' que é executada no contexto isolado.
    """
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=headless)
        context = browser.new_context()
        activate(context)
        context.close()
        browser.close()