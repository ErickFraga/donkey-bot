import os
import json
from datetime import datetime
import pandas as pd
import numpy as np
from dotenv import load_dotenv
from binance.client import Client
from .telegram_notifier import TelegramNotifier
from .order_manager import OrderManager
from .logger import Logger
from .chart_manager import ChartManager

# Carregar variáveis de ambiente
load_dotenv()

class TradingManager:
    def __init__(self, is_backtest=False):
        """Inicializa o TradingManager"""
        # Configurações gerais
        self.symbol = os.getenv('SYMBOL', 'BTCUSDT')
        self.quantity = float(os.getenv('QUANTITY', '0.00010'))  # valor padrão caso não encontre
        self.env = os.getenv('ENV', 'DEV').upper()
        self.is_dev = self.env == 'DEV'
        self.is_backtest = is_backtest
        
        # Configurar stop loss e take profit a partir do .env
        self.stop_loss_percent = float(os.getenv('STOP_LOSS_PERCENT', '2.0')) / 100
        self.take_profit_percent = float(os.getenv('TAKE_PROFIT_PERCENT', '3.0')) / 100
        
        # Moving averages settings
        self.ma_short_period = 9
        self.ma_long_period = 21
        
        # Estado do trading
        self.current_position = None
        self.stop_loss_price = None
        self.take_profit_price = None
        
        # Métricas e resultados
        self.orders = []
        self.initial_balance = 1000.0
        self.current_balance = self.initial_balance
        
        # Log das configurações
        self.logger = Logger(prefix='backtest' if is_backtest else '')
        self.logger.info("\n" + "="*50)
        self.logger.info("Configurações do Trading Manager:")
        self.logger.info(f"Symbol: {self.symbol}")
        self.logger.info(f"Quantity: {self.quantity}")
        self.logger.info(f"Stop Loss: {self.stop_loss_percent*100:.1f}%")
        self.logger.info(f"Take Profit: {self.take_profit_percent*100:.1f}%")
        self.logger.info(f"Ambiente: {self.env}")
        self.logger.info("="*50 + "\n")
        
        # Configurar componentes
        if not is_backtest:
            self.client = Client(
                os.getenv('BINANCE_API_KEY'),
                os.getenv('BINANCE_API_SECRET')
            )
            self.telegram = TelegramNotifier()
            
        self.order_manager = OrderManager(prefix='backtest' if is_backtest else '')
        self.chart_manager = ChartManager(prefix='backtest' if is_backtest else '')

    def calculate_indicators(self, df):
        """Calcula os indicadores técnicos"""
        # Médias móveis
        df['MA_short'] = df['close'].rolling(window=self.ma_short_period).mean()
        df['MA_long'] = df['close'].rolling(window=self.ma_long_period).mean()
        
        # Calcular ATR (Average True Range) para volatilidade
        df['TR'] = np.maximum(
            df['high'] - df['low'],
            np.maximum(
                abs(df['high'] - df['close'].shift(1)),
                abs(df['low'] - df['close'].shift(1))
            )
        )
        df['ATR'] = df['TR'].rolling(window=14).mean()
        
        return df

    def calculate_dynamic_stops(self, current_price, atr_value, trend_strength):
        """Calcula stop loss e take profit dinâmicos baseados na volatilidade e tendência
        
        Args:
            current_price (float): Preço atual
            atr_value (float): Valor do ATR (volatilidade)
            trend_strength (float): Força da tendência em percentual
        """
        # Base stop loss e take profit do .env
        base_sl_percent = self.stop_loss_percent
        base_tp_percent = self.take_profit_percent
        
        # Ajustar stop loss baseado na volatilidade (ATR)
        # Se volatilidade alta, aumenta a distância do stop loss
        volatility_factor = atr_value / current_price
        sl_volatility_multiplier = 1 + (volatility_factor * 10)  # Aumenta SL em alta volatilidade
        
        # Ajustar take profit baseado na força da tendência
        # Tendência mais forte = take profit mais distante
        tp_trend_multiplier = 1 + (abs(trend_strength) / 100)
        
        # Calcular stops finais
        dynamic_sl_percent = base_sl_percent * sl_volatility_multiplier
        dynamic_tp_percent = base_tp_percent * tp_trend_multiplier
        
        # Limitar os valores para evitar extremos
        dynamic_sl_percent = min(max(dynamic_sl_percent, 0.005), 0.05)  # Entre 0.5% e 5%
        dynamic_tp_percent = min(max(dynamic_tp_percent, 0.01), 0.10)   # Entre 1% e 10%
        
        # Calcular preços
        stop_loss_price = current_price * (1 - dynamic_sl_percent)
        take_profit_price = current_price * (1 + dynamic_tp_percent)
        
        return stop_loss_price, take_profit_price, dynamic_sl_percent, dynamic_tp_percent

    def check_signals(self, candle, ma_short_current, ma_long_current, ma_short_previous, ma_long_previous):
        """Verifica sinais de compra e venda"""
        current_price = float(candle['close'])
        
        # Calcular força da tendência
        trend_strength = (ma_short_current - ma_long_current) / ma_long_current * 100
        
        # Atualizar gráfico
        self.chart_manager.update_data(
            current_price=current_price,
            ma_short=ma_short_current,
            ma_long=ma_long_current,
            open_price=float(candle['open']),
            high_price=float(candle['high']),
            low_price=float(candle['low']),
            stop_loss=self.stop_loss_price,
            take_profit=self.take_profit_price
        )
        
        # Verificar sinais
        if not self.current_position:
            # Sinal de compra: média curta cruza a longa para cima E preço acima das duas médias
            if (ma_short_current > ma_long_current and 
                ma_short_previous < ma_long_previous and
                current_price > ma_short_current and
                current_price > ma_long_current):
                
                # Calcular stops dinâmicos
                stop_loss, take_profit, sl_pct, tp_pct = self.calculate_dynamic_stops(
                    current_price,
                    float(candle.get('ATR', current_price * 0.02)),  # Default 2% se ATR não disponível
                    trend_strength
                )
                
                # Executar compra com stops dinâmicos
                self.execute_buy(
                    current_price, 
                    candle['timestamp'],
                    stop_loss,
                    take_profit,
                    sl_pct,
                    tp_pct
                )
        else:
            # Verificar condições de saída em ordem de prioridade
            if current_price <= self.stop_loss_price:
                # 1. Stop Loss - proteção contra grandes perdas
                self.execute_sell(current_price, candle['timestamp'], "Stop Loss")
            elif current_price >= self.take_profit_price:
                # 2. Take Profit atingido
                self.execute_sell(current_price, candle['timestamp'], "Take Profit")
            elif ma_short_current < ma_long_current:
                # 3. Média curta abaixo da longa - tendência de baixa
                self.execute_sell(current_price, candle['timestamp'], "Tendência de Baixa")
            elif trend_strength < 0.05:
                # 4. Força da tendência muito fraca
                self.execute_sell(current_price, candle['timestamp'], "Tendência Fraca")
            elif current_price < ma_short_current:
                # 5. Preço abaixo da média curta
                self.execute_sell(current_price, candle['timestamp'], "Preço < Média Curta")
            else:
                # Atualizar stops dinâmicos se ainda estiver na posição
                new_sl, new_tp, _, _ = self.calculate_dynamic_stops(
                    current_price,
                    float(candle.get('ATR', current_price * 0.02)),
                    trend_strength
                )
                
                # Só atualiza o stop loss se o novo for maior que o atual (trailing stop)
                if new_sl > self.stop_loss_price:
                    self.stop_loss_price = new_sl
                    self.logger.info(f"Stop Loss atualizado: ${new_sl:.2f}")
                
                # Atualiza take profit se a tendência estiver forte
                if trend_strength > 0.1 and new_tp > self.take_profit_price:
                    self.take_profit_price = new_tp
                    self.logger.info(f"Take Profit atualizado: ${new_tp:.2f}")

    def execute_buy(self, price, timestamp, stop_loss_price=None, take_profit_price=None, sl_percent=None, tp_percent=None):
        """Executa uma ordem de compra"""
        # Calcular quantidade baseada no saldo disponível (1% de margem para taxas)
        amount = (self.current_balance * 0.99) / price
        cost = amount * price
        
        # Se não fornecidos, usar valores padrão
        if stop_loss_price is None:
            stop_loss_price = price * (1 - self.stop_loss_percent)
            sl_percent = self.stop_loss_percent
            
        if take_profit_price is None:
            take_profit_price = price * (1 + self.take_profit_percent)
            tp_percent = self.take_profit_percent
        
        # Registrar a ordem
        order = {
            'type': 'buy',
            'timestamp': timestamp,
            'price': price,
            'amount': amount,
            'cost': cost,
            'balance_before': self.current_balance,
            'balance_after': self.current_balance - cost,
            'stop_loss': stop_loss_price,
            'take_profit': take_profit_price
        }
        self.orders.append(order)
        
        # Atualizar saldo e posição
        self.current_balance -= cost
        self.current_position = {
            'entry_price': price,
            'amount': amount,
            'stop_loss': stop_loss_price,
            'take_profit': take_profit_price
        }
        
        # Atualizar preços de stop loss e take profit
        self.stop_loss_price = stop_loss_price
        self.take_profit_price = take_profit_price
        
        # Registrar no log
        self.logger.info(f"Compra executada - Preço: ${price:.2f}, Quantidade: {amount:.8f}")
        self.logger.info(f"Stop Loss: ${stop_loss_price:.2f} ({sl_percent*100:.1f}%)")
        self.logger.info(f"Take Profit: ${take_profit_price:.2f} ({tp_percent*100:.1f}%)")
        
        # Adicionar ponto de compra no gráfico
        self.chart_manager.add_buy_point(price)
        
        # Notificar via Telegram se não for backtest
        if not self.is_backtest:
            self.telegram.send_message(
                f"🟢 Donkey Bot - Ordem de compra executada{' [DEV]' if self.is_dev else ''}\n"
                f"Preço: ${price:.2f}\n"
                f"Stop Loss: ${stop_loss_price:.2f}\n"
                f"Take Profit: ${take_profit_price:.2f}"
            )

    def execute_sell(self, price, timestamp, reason=""):
        """Executa uma ordem de venda"""
        if not self.current_position:
            return
            
        # Calcular resultado
        amount = self.current_position['amount']
        entry_price = self.current_position['entry_price']
        revenue = amount * price
        profit = revenue - (amount * entry_price)
        profit_percentage = (price - entry_price) / entry_price * 100
        
        # Registrar a ordem
        order = {
            'type': 'sell',
            'timestamp': timestamp,
            'price': price,
            'amount': amount,
            'revenue': revenue,
            'profit': profit,
            'profit_percentage': profit_percentage,
            'reason': reason,
            'balance_before': self.current_balance,
            'balance_after': self.current_balance + revenue
        }
        self.orders.append(order)
        
        # Atualizar saldo e posição
        self.current_balance += revenue
        
        # Registrar no log
        self.logger.info(f"Venda executada ({reason}) - Preço: ${price:.2f}, Resultado: ${profit:.2f} ({profit_percentage:.2f}%)")
        self.logger.info(f"Saldo atual: ${self.current_balance:.2f}")
        
        # Adicionar ponto de venda no gráfico
        self.chart_manager.add_sell_point(price)
        
        # Notificar via Telegram se não for backtest
        if not self.is_backtest:
            self.telegram.send_message(
                f"🔴 Donkey Bot - Ordem de venda executada ({reason}){' [DEV]' if self.is_dev else ''}\n"
                f"Preço: ${price:.2f}\n"
                f"Lucro: ${profit:.2f} ({profit_percentage:.2f}%)"
            )
        
        # Limpar posição atual
        self.current_position = None
        self.stop_loss_price = None
        self.take_profit_price = None

    def check_stop_loss_take_profit(self, current_price, current_time):
        """Verifica se atingiu stop loss"""
        if current_price <= self.stop_loss_price:
            self.execute_sell(current_price, current_time, "Stop Loss")

    def run_simulation(self, data):
        """Executa uma simulação com dados históricos"""
        self.is_backtest = True
        
        # Converter dados para DataFrame
        df = pd.DataFrame(data)
        
        # Calcular indicadores
        df = self.calculate_indicators(df)
        
        # Remover linhas com NaN
        df = df.dropna()
        
        # Iterar sobre os dados
        for i in range(2, len(df)):
            candle = {
                'timestamp': df['timestamp'].iloc[i],
                'open': df['open'].iloc[i],
                'high': df['high'].iloc[i],
                'low': df['low'].iloc[i],
                'close': df['close'].iloc[i],
                'volume': df['volume'].iloc[i]
            }
            
            # Obter valores dos indicadores
            ma_short_current = df['MA_short'].iloc[i]
            ma_long_current = df['MA_long'].iloc[i]
            ma_short_previous = df['MA_short'].iloc[i-2]
            ma_long_previous = df['MA_long'].iloc[i-2]
            
            # Verificar sinais
            self.check_signals(candle, ma_short_current, ma_long_current, ma_short_previous, ma_long_previous)
        
        # Calcular métricas finais
        metrics = self.calculate_metrics()
        
        # Salvar gráfico final
        self.chart_manager.save_chart()
        
        return {
            'orders': self.orders,
            'metrics': metrics
        }

    def calculate_metrics(self):
        """Calcula métricas do trading"""
        if not self.orders:
            return None
            
        # Métricas gerais
        total_trades = len([order for order in self.orders if order['type'] == 'sell'])
        winning_trades = len([order for order in self.orders if order['type'] == 'sell' and order['profit'] > 0])
        losing_trades = len([order for order in self.orders if order['type'] == 'sell' and order['profit'] < 0])
        
        # Métricas de lucro/prejuízo
        total_profit = sum([order['profit'] for order in self.orders if order['type'] == 'sell' and order['profit'] > 0])
        total_loss = sum([order['profit'] for order in self.orders if order['type'] == 'sell' and order['profit'] < 0])
        net_profit = total_profit + total_loss
        
        # Calcular win rate
        win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0
        
        # Calcular profit factor
        profit_factor = abs(total_profit / total_loss) if total_loss != 0 else float('inf')
        
        # Calcular drawdown
        balances = [self.initial_balance]
        for order in self.orders:
            if order['type'] == 'sell':
                balances.append(order['balance_after'])
        
        running_max = np.maximum.accumulate(balances)
        drawdowns = (running_max - balances) / running_max * 100
        max_drawdown = max(drawdowns)
        
        # Calcular tempo em trades
        if len(self.orders) >= 2:
            first_trade = min(order['timestamp'] for order in self.orders)
            last_trade = max(order['timestamp'] for order in self.orders)
            trading_time = last_trade - first_trade
            trades_per_day = total_trades / (trading_time.days + trading_time.seconds / 86400)
        else:
            trading_time = datetime.now() - datetime.now()
            trades_per_day = 0
        
        return {
            'general': {
                'total_trades': total_trades,
                'winning_trades': winning_trades,
                'losing_trades': losing_trades,
                'win_rate': win_rate
            },
            'profit_loss': {
                'initial_balance': self.initial_balance,
                'final_balance': self.current_balance,
                'net_profit': net_profit,
                'net_profit_percentage': (net_profit / self.initial_balance * 100),
                'profit_factor': profit_factor,
                'average_profit_per_trade': net_profit / total_trades if total_trades > 0 else 0
            },
            'risk': {
                'max_drawdown': max_drawdown,
                'risk_reward_ratio': abs(total_profit / total_loss) if total_loss != 0 else float('inf')
            },
            'time': {
                'trading_time': str(trading_time),
                'trades_per_day': trades_per_day
            }
        } 