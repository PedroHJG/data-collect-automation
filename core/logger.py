import logging
import os

log_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "logs")
os.makedirs(log_dir, exist_ok=True)

logger = logging.getLogger("PraContar")
logger.setLevel(logging.DEBUG)

# File handler para os logs detalhados
fh = logging.FileHandler(os.path.join(log_dir, "app.log"), encoding='utf-8')
fh.setLevel(logging.DEBUG)

# Console handler para mensagens críticas no terminal
ch = logging.StreamHandler()
ch.setLevel(logging.ERROR)

formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
fh.setFormatter(formatter)
ch.setFormatter(formatter)

logger.addHandler(fh)
logger.addHandler(ch)

def get_logger():
    return logger
