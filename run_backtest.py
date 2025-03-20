from datetime import datetime, timedelta
from dotenv import load_dotenv
from trading_bot.backtest_manager import BacktestManager
from trading_bot.trading_manager import TradingManager
from binance.client import Client

# Carregar variáveis de ambiente
load_dotenv()

def main():
    # Configurar período do backtest
    end_date = datetime.now()
    start_date = end_date - timedelta(days=90)  # últimos 30 dias
    
    # Criar instância do BacktestManager
    backtest = BacktestManager(
        symbol="BTCUSDT",
        start_date=start_date,
        end_date=end_date,
        interval=Client.KLINE_INTERVAL_15MINUTE  # candles de 15 minutos
    )
    
    # Criar instância do TradingManager em modo backtest
    trading = TradingManager(is_backtest=True)
    
    # Executar backtest
    results = backtest.run_backtest(trading)
    
    # Os resultados (orders e metrics) já foram logados pelo BacktestManager
    # e o gráfico foi salvo pelo TradingManager
    
if __name__ == "__main__":
    main() 