import os
import time
from dotenv import load_dotenv
from trading_bot.trading_manager import TradingManager
from trading_bot.logger import Logger

def main():
    # Load environment variables
    load_dotenv()
    
    # Initialize logger
    logger = Logger()
    logger.log_info("Starting trading bot...")
    
    # Initialize trading manager
    trading_manager = TradingManager()
    
    try:
        while True:
            # Check trading signals
            trading_manager.check_signals()
            
            # Wait 1 minute before next check
            time.sleep(10)
            
    except KeyboardInterrupt:
        logger.log_info("Bot stopped by user")
    except Exception as e:
        logger.log_error(f"Unexpected error: {str(e)}")
        
if __name__ == "__main__":
    main() 