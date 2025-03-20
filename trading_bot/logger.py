import logging
import os
from datetime import datetime

class Logger:
    def __init__(self):
        self.setup_logger()

    def setup_logger(self):
        """Configura o logger do sistema"""
        # Cria o diretório de logs se não existir
        os.makedirs("logs", exist_ok=True)
        
        # Nome do arquivo de log com a data atual
        log_file = f"logs/donkey_bot_{datetime.now().strftime('%Y%m%d')}.log"
        
        # Configura o logger
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )
        
        self.logger = logging.getLogger(__name__)

    def log_info(self, mensagem):
        """Registra uma mensagem de informação"""
        self.logger.info(mensagem)

    def log_error(self, mensagem):
        """Registra uma mensagem de erro"""
        self.logger.error(mensagem)

    def log_warning(self, mensagem):
        """Registra uma mensagem de aviso"""
        self.logger.warning(mensagem)

    def log_debug(self, mensagem):
        """Registra uma mensagem de debug"""
        self.logger.debug(mensagem) 