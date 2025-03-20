import os
from datetime import datetime, timedelta
from dotenv import load_dotenv
from trading_bot.backtest_manager import BacktestManager

def main():
    # Carregar variáveis de ambiente
    load_dotenv()
    
    # Configurar período do backtest
    end_date = datetime.now()
    start_date = end_date - timedelta(days=30)  # 7 dias de backtest
    
    # Configurar parâmetros do backtest
    symbol = "BTCUSDT"
    initial_balance = 1000.0  # 1000 USDT
    
    # Criar e executar backtest
    backtest = BacktestManager(
        symbol=symbol,
        initial_balance=initial_balance,
        start_date=start_date,
        end_date=end_date
    )
    
    # Executar backtest
    backtest.execute_backtest()

if __name__ == "__main__":
    main() 