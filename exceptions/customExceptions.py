class BaseAutomationException(Exception):
    """Classe base para erros da automação que serão exibidos ao usuário."""
    pass

class BrowserException(BaseAutomationException):
    """Erros de inicialização do navegador."""
    pass

class ConnectionException(BaseAutomationException):
    """Erros de login ou redirecionamento de rede."""
    pass

class DataCollectionException(BaseAutomationException):
    """Erros de raspagem (elementos não encontrados, timeout)."""
    pass

class DataCleaningException(BaseAutomationException):
    """Erros de conversão do Pandas ou salvamento no Excel."""
    pass
