import os
from dotenv import load_dotenv

load_dotenv()

def buscar_credenciais():
    return {
        "usuario": os.getenv("MAPIA_LOGIN"),
        "senha": os.getenv("MAPIA_SENHA"),
        "caminho_planilha": os.getenv("CAMINHO_PLANILHA_ATUALIZAR"),
    }