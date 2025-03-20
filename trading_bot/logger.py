import os
import logging
from datetime import datetime

class Logger:
    _instances = {}  # Dicionário para armazenar instâncias únicas do logger

    def __init__(self, prefix=''):
        """Inicializa o logger
        
        Args:
            prefix (str): Prefixo para o nome do arquivo de log
        """
        # Se já existe um logger com este prefixo, reutiliza
        if prefix in Logger._instances:
            self.logger = Logger._instances[prefix]
            return

        # Criar diretório de logs se não existir
        if not os.path.exists('logs'):
            os.makedirs('logs')
            
        # Configurar nome do arquivo
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        prefix_str = f"{prefix}_" if prefix else ""
        log_file = f"logs/{prefix_str}donkey_bot_{timestamp}.log"
        
        # Configurar logger
        logger_name = f"donkey_bot_{prefix}"
        self.logger = logging.getLogger(logger_name)
        
        # Se o logger já tem handlers, não configura novamente
        if not self.logger.handlers:
            self.logger.setLevel(logging.INFO)
            
            # Configurar formato do log
            formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
            
            # Handler para arquivo
            file_handler = logging.FileHandler(log_file)
            file_handler.setFormatter(formatter)
            self.logger.addHandler(file_handler)
            
            # Handler para console
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(formatter)
            self.logger.addHandler(console_handler)
            
            # Evitar propagação para o logger root
            self.logger.propagate = False
        
        # Armazenar a instância para reutilização
        Logger._instances[prefix] = self.logger

    def info(self, message):
        """Registra uma mensagem de informação"""
        self.logger.info(message)
        
    def error(self, message):
        """Registra uma mensagem de erro"""
        self.logger.error(message)
        
    def warning(self, message):
        """Registra uma mensagem de aviso"""
        self.logger.warning(message)
    
    def debug(self, message):
        """Registra mensagem de debug"""
        self.logger.debug(message)
    
    def critical(self, message):
        """Registra mensagem crítica"""
        self.logger.critical(message) 