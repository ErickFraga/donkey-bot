import os
import json
from datetime import datetime
import pandas as pd
import numpy as np
from binance.client import Client
from .telegram_notifier import TelegramNotifier
from .order_manager import OrderManager
from .logger import Logger

class TradingManager:
    def __init__(self):
        self.client = Client(
            os.getenv('BINANCE_API_KEY'),
            os.getenv('BINANCE_API_SECRET')
        )
        self.symbol = os.getenv('SYMBOL')
        self.quantity = float(os.getenv('QUANTITY'))
        self.env = os.getenv('ENV', 'DEV').upper()
        self.is_dev = self.env == 'DEV'
        self.telegram = TelegramNotifier()
        self.order_manager = OrderManager()
        self.logger = Logger()
        
        # Moving averages settings
        self.short_window = 8
        self.long_window = 21
        
        # Stop loss and take profit settings
        self.stop_loss_percent = 0.02  # 2%
        self.take_profit_percent = 0.03  # 3%
        
        self.current_position = None
        self.stop_loss_price = None
        self.take_profit_price = None
        
        # Log environment
        self.logger.log_info(f"Running in {self.env} environment")

    def calculate_moving_averages(self):
        """Calculate short and long moving averages"""
        klines = self.client.get_historical_klines(
            self.symbol,
            Client.KLINE_INTERVAL_1MINUTE,
            f"{self.long_window + 2} minutes ago UTC"
        )
        
        df = pd.DataFrame(klines, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume', 'close_time', 'quote_av', 'trades', 'tb_base_av', 'tb_quote_av', 'ignore'])
        df['close'] = pd.to_numeric(df['close'])
        
        df['MA_short'] = df['close'].rolling(window=self.short_window).mean()
        df['MA_long'] = df['close'].rolling(window=self.long_window).mean()
        
        return df

    def check_signals(self):
        """Check for buy and sell signals"""
        df = self.calculate_moving_averages()
        
        if len(df) < self.long_window + 2:
            return None
            
        current_price = float(df['close'].iloc[-1])
        ma_short_current = df['MA_short'].iloc[-1]
        ma_long_current = df['MA_long'].iloc[-1]
        ma_short_previous = df['MA_short'].iloc[-3]
        ma_long_previous = df['MA_long'].iloc[-3]
        
        # Print market data
        print("\n" + "="*50)
        print(f"📊 {self.symbol} Market Data{' [DEV]' if self.is_dev else ''}")
        print(f"💰 Preço Atual: {current_price:.2f}")
        print(f"📈 Média Curta (8): {ma_short_current:.2f}")
        print(f"📉 Média Longa (21): {ma_long_current:.2f}")
        if self.current_position:
            print(f"🎯 Stop Loss: {self.stop_loss_price:.2f}")
            print(f"🎯 Take Profit: {self.take_profit_price:.2f}")
        print("="*50 + "\n")
        
        # Buy signal
        if (ma_short_current > ma_long_current and 
            ma_short_previous < ma_long_previous and 
            not self.current_position):
            self.execute_buy(current_price)
            
        # Check stop loss and take profit
        elif self.current_position:
            self.check_stop_loss_take_profit(current_price)

    def execute_buy(self, entry_price):
        """Execute a buy order"""
        try:
            if self.is_dev:
                # Simulate order in dev mode
                order = {
                    'orderId': f"dev_{datetime.now().timestamp()}",
                    'symbol': self.symbol,
                    'side': Client.SIDE_BUY,
                    'executedQty': self.quantity,
                    'cummulativeQuoteQty': entry_price * self.quantity,
                    'status': 'FILLED'
                }
                self.logger.log_info("[DEV] Simulated buy order")
            else:
                order = self.client.create_order(
                    symbol=self.symbol,
                    side=Client.SIDE_BUY,
                    type=Client.ORDER_TYPE_MARKET,
                    quantity=self.quantity
                )
            
            self.current_position = {
                'entry_price': entry_price,
                'quantity': self.quantity,
                'timestamp': datetime.now().isoformat()
            }
            
            self.stop_loss_price = entry_price * (1 - self.stop_loss_percent)
            self.take_profit_price = entry_price * (1 + self.take_profit_percent)
            
            # Save order and notify
            self.order_manager.save_order(order)
            self.telegram.send_message(
                f"🟢 Buy order executed{' [DEV]' if self.is_dev else ''}\n"
                f"Price: {entry_price}\n"
                f"Stop Loss: {self.stop_loss_price}\n"
                f"Take Profit: {self.take_profit_price}"
            )
            self.logger.log_info(f"Buy executed - Price: {entry_price}")
            
        except Exception as e:
            self.logger.log_error(f"Error executing buy order: {str(e)}")
            self.telegram.send_message(f"❌ Error executing buy order: {str(e)}")

    def execute_sell(self, current_price, reason):
        """Execute a sell order"""
        try:
            if self.is_dev:
                # Simulate order in dev mode
                order = {
                    'orderId': f"dev_{datetime.now().timestamp()}",
                    'symbol': self.symbol,
                    'side': Client.SIDE_SELL,
                    'executedQty': self.quantity,
                    'cummulativeQuoteQty': current_price * self.quantity,
                    'status': 'FILLED'
                }
                self.logger.log_info("[DEV] Simulated sell order")
            else:
                order = self.client.create_order(
                    symbol=self.symbol,
                    side=Client.SIDE_SELL,
                    type=Client.ORDER_TYPE_MARKET,
                    quantity=self.quantity
                )
            
            profit = (current_price - self.current_position['entry_price']) * self.quantity
            profit_percentage = (current_price / self.current_position['entry_price'] - 1) * 100
            
            # Save order and notify
            self.order_manager.save_order(order)
            self.telegram.send_message(
                f"🔴 Sell order executed ({reason}){' [DEV]' if self.is_dev else ''}\n"
                f"Price: {current_price}\n"
                f"Profit: {profit:.2f} USDT ({profit_percentage:.2f}%)"
            )
            self.logger.log_info(f"Sell executed - Price: {current_price}, Reason: {reason}")
            
            self.current_position = None
            self.stop_loss_price = None
            self.take_profit_price = None
            
        except Exception as e:
            self.logger.log_error(f"Error executing sell order: {str(e)}")
            self.telegram.send_message(f"❌ Error executing sell order: {str(e)}")

    def check_stop_loss_take_profit(self, current_price):
        """Check if stop loss or take profit is hit"""
        if not self.current_position:
            return
            
        if current_price <= self.stop_loss_price:
            self.execute_sell(current_price, "Stop Loss")
            
        elif current_price >= self.take_profit_price:
            # Update stop loss and take profit
            new_stop_loss = self.take_profit_price * (1 - self.stop_loss_percent)
            new_take_profit = self.take_profit_price * (1 + self.take_profit_percent)
            
            self.stop_loss_price = new_stop_loss
            self.take_profit_price = new_take_profit
            
            self.telegram.send_message(
                f"📈 Take Profit hit!{' [DEV]' if self.is_dev else ''}\n"
                f"New Stop Loss: {new_stop_loss}\n"
                f"New Take Profit: {new_take_profit}"
            )
            self.logger.log_info("Take Profit hit - Updating levels") 