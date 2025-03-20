import os
import pandas as pd
from datetime import datetime, timedelta
from dotenv import load_dotenv
from binance.client import Client
from .logger import Logger

# Carregar variáveis de ambiente
load_dotenv()

class BacktestManager:
    def __init__(self, symbol, start_date=None, end_date=None, interval=Client.KLINE_INTERVAL_15MINUTE):
        """Inicializa o BacktestManager
        
        Args:
            symbol (str): Par de trading (ex: 'BTCUSDT')
            start_date (datetime, opcional): Data inicial do backtest. Se None, usa 7 dias atrás
            end_date (datetime, opcional): Data final do backtest. Se None, usa data atual
            interval (str, opcional): Intervalo dos candles. Padrão: 15 minutos
        """
        # Configurar cliente Binance
        self.client = Client(
            os.getenv('BINANCE_API_KEY'),
            os.getenv('BINANCE_API_SECRET')
        )
        self.symbol = symbol
        self.interval = interval
        
        # Configurar datas do backtest
        if start_date is None:
            start_date = datetime.now() - timedelta(days=7)
        if end_date is None:
            end_date = datetime.now()
            
        self.start_date = start_date
        self.end_date = end_date
        
        # Configurar logger
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.logger = Logger("backtest")
        
        # Obter dados históricos
        self.historical_data = None

    def get_historical_data(self):
        """Obtém dados históricos da Binance
        
        Returns:
            pd.DataFrame: DataFrame com os dados históricos
        """
        try:
            self.logger.info(f"Obtendo dados históricos para {self.symbol}")
            self.logger.info(f"Período: {self.start_date} até {self.end_date}")
            self.logger.info(f"Intervalo: {self.interval}")
            
            # Obter dados da Binance
            klines = self.client.get_historical_klines(
                self.symbol,
                self.interval,
                self.start_date.strftime("%d %b %Y %H:%M:%S"),
                self.end_date.strftime("%d %b %Y %H:%M:%S")
            )
            
            # Criar DataFrame
            df = pd.DataFrame(klines, columns=[
                'timestamp', 'open', 'high', 'low', 'close', 'volume',
                'close_time', 'quote_av', 'trades', 'tb_base_av',
                'tb_quote_av', 'ignore'
            ])
            
            # Converter tipos de dados
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            for col in ['open', 'high', 'low', 'close', 'volume']:
                df[col] = pd.to_numeric(df[col], errors='coerce')
            
            # Remover colunas desnecessárias
            df = df[['timestamp', 'open', 'high', 'low', 'close', 'volume']]
            
            self.historical_data = df
            self.logger.info(f"Dados obtidos com sucesso: {len(df)} candles")
            
            return df
            
        except Exception as e:
            self.logger.error(f"Erro ao obter dados históricos: {str(e)}")
            raise e

    def prepare_backtest_data(self):
        """Prepara os dados para o backtest
        
        Returns:
            list: Lista de dicionários com os dados dos candles
        """
        if self.historical_data is None:
            self.get_historical_data()
            
        data = []
        
        for _, row in self.historical_data.iterrows():
            candle = {
                'timestamp': row['timestamp'],
                'open': float(row['open']),
                'high': float(row['high']),
                'low': float(row['low']),
                'close': float(row['close']),
                'volume': float(row['volume'])
            }
            data.append(candle)
            
        return data

    def run_backtest(self, trading_manager):
        """Executa o backtest usando o TradingManager
        
        Args:
            trading_manager: Instância do TradingManager configurada para backtest
            
        Returns:
            dict: Resultados do backtest (ordens e métricas)
        """
        # Preparar dados
        data = self.prepare_backtest_data()
        
        # Log do início do backtest
        self.logger.info("\n" + "="*50)
        self.logger.info("Iniciando Backtest")
        self.logger.info(f"Symbol: {self.symbol}")
        self.logger.info(f"Período: {self.start_date} até {self.end_date}")
        self.logger.info(f"Intervalo: {self.interval}")
        self.logger.info(f"Total de candles: {len(data)}")
        self.logger.info("="*50 + "\n")
        
        # Executar simulação
        results = trading_manager.run_simulation(data)
        
        # Log do fim do backtest
        self.logger.info("\n" + "="*50)
        self.logger.info("Backtest Finalizado")
        
        # Log das métricas
        metrics = results['metrics']
        if metrics:
            self.logger.info("\nMétricas Gerais:")
            self.logger.info(f"Total de trades: {metrics['general']['total_trades']}")
            self.logger.info(f"Win rate: {metrics['general']['win_rate']:.2f}%")
            self.logger.info(f"Profit factor: {metrics['profit_loss']['profit_factor']:.2f}")
            self.logger.info(f"Drawdown máximo: {metrics['risk']['max_drawdown']:.2f}%")
            self.logger.info(f"Lucro líquido: ${metrics['profit_loss']['net_profit']:.2f} ({metrics['profit_loss']['net_profit_percentage']:.2f}%)")
        
        self.logger.info("="*50 + "\n")
        
        return results 