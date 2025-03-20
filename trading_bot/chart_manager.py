import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.io as pio
import pandas as pd
import numpy as np
from datetime import datetime
import os

class ChartManager:
    def __init__(self, prefix=''):
        # Criar diretório para salvar os gráficos
        os.makedirs("charts", exist_ok=True)
        
        # Gerar nome do arquivo com timestamp
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        prefix_str = f"{prefix}_" if prefix else ""
        self.chart_file = f"charts/{prefix_str}chart_{self.timestamp}.html"
        
        # Dados para o gráfico
        self.times = []
        self.open_prices = []
        self.high_prices = []
        self.low_prices = []
        self.close_prices = []
        self.ma_short = []
        self.ma_long = []
        
        # Dados para marcadores de ordem
        self.buy_points_x = []
        self.buy_points_y = []
        self.sell_points_x = []
        self.sell_points_y = []
        
        # Dados para stop loss e take profit
        self.stop_loss = None
        self.take_profit = None
        self.in_position = False
        
        # Limite de pontos no gráfico (aumentado para 1000)
        self.max_points = 1000000
        
        # Criar figura do Plotly
        self.fig = go.Figure()
        self._setup_layout()
        
        # Salvar gráfico inicial
        self.save_chart()

    def _setup_layout(self):
        """Configura o layout do gráfico"""
        self.fig.update_layout(
            title='Donkey Bot - Análise Técnica',
            title_x=0.5,
            plot_bgcolor='#131722',
            paper_bgcolor='#131722',
            font=dict(
                color='#787B86',
                family='Trebuchet MS'
            ),
            showlegend=True,
            xaxis=dict(
                showgrid=True,
                gridcolor='rgba(42, 46, 57, 0.8)',
                tickfont=dict(color='#787B86'),
                type='date',
                tickformat='%H:%M',
                rangeslider=dict(visible=False),
                title=None,
                autorange=True,  # Ajuste automático do range do eixo X
                showspikes=True,  # Mostra linhas guia ao passar o mouse
                spikemode='across',
                spikesnap='cursor',
                showline=True,
                linewidth=1,
                linecolor='rgba(42, 46, 57, 0.8)'
            ),
            yaxis=dict(
                showgrid=True,
                gridcolor='rgba(42, 46, 57, 0.8)',
                tickfont=dict(color='#787B86'),
                title=None,
                side='right',
                autorange=True,  # Ajuste automático do range do eixo Y
                showspikes=True,  # Mostra linhas guia ao passar o mouse
                spikemode='across',
                spikesnap='cursor',
                showline=True,
                linewidth=1,
                linecolor='rgba(42, 46, 57, 0.8)'
            ),
            margin=dict(l=50, r=50, t=50, b=50),  # Margens ajustadas
            autosize=True,  # Ajuste automático do tamanho
            height=800,  # Altura fixa
            width=1200,  # Largura fixa
            hovermode='x unified',
            dragmode='pan',
            modebar=dict(
                bgcolor='rgba(19, 23, 34, 0.8)',
                color='#787B86',
                activecolor='#2962FF'
            ),
            legend=dict(
                yanchor="top",
                y=0.99,
                xanchor="left",
                x=0.01,
                bgcolor='rgba(19, 23, 34, 0.8)',
                bordercolor='#2A2E39',
                borderwidth=1
            )
        )

    def update_data(self, current_price, ma_short, ma_long, open_price=None, high_price=None, low_price=None, stop_loss=None, take_profit=None):
        """Atualiza os dados do gráfico"""
        current_time = datetime.now()
        
        # Se não fornecidos, usar valores apropriados
        if open_price is None:
            open_price = current_price
        if high_price is None:
            high_price = max(current_price, open_price)
        if low_price is None:
            low_price = min(current_price, open_price)
        
        # Converter para float e garantir que os valores façam sentido
        open_price = float(open_price)
        high_price = float(max(high_price, open_price, current_price))
        low_price = float(min(low_price, open_price, current_price))
        current_price = float(current_price)
        ma_short = float(ma_short)
        ma_long = float(ma_long)
        
        # Adicionar novos dados
        self.times.append(current_time)
        self.open_prices.append(open_price)
        self.high_prices.append(high_price)
        self.low_prices.append(low_price)
        self.close_prices.append(current_price)
        self.ma_short.append(ma_short)
        self.ma_long.append(ma_long)
        
        # Atualizar stop loss e take profit
        self.stop_loss = float(stop_loss) if stop_loss is not None else None
        self.take_profit = float(take_profit) if take_profit is not None else None
        
        # Limitar o número de pontos apenas se exceder muito o máximo
        if len(self.times) > self.max_points * 1.5:
            excess = len(self.times) - self.max_points
            self.times = self.times[excess:]
            self.open_prices = self.open_prices[excess:]
            self.high_prices = self.high_prices[excess:]
            self.low_prices = self.low_prices[excess:]
            self.close_prices = self.close_prices[excess:]
            self.ma_short = self.ma_short[excess:]
            self.ma_long = self.ma_long[excess:]
            
            # Atualizar pontos de compra e venda
            for i in range(len(self.buy_points_x)):
                if self.buy_points_x[i] < self.times[0]:
                    self.buy_points_x.pop(i)
                    self.buy_points_y.pop(i)
                    
            for i in range(len(self.sell_points_x)):
                if self.sell_points_x[i] < self.times[0]:
                    self.sell_points_x.pop(i)
                    self.sell_points_y.pop(i)
        
        # Atualizar gráfico
        self.fig = go.Figure()
        self._setup_layout()

        # Criar DataFrame com os dados dos candles
        df = pd.DataFrame({
            'time': self.times,
            'open': self.open_prices,
            'high': self.high_prices,
            'low': self.low_prices,
            'close': self.close_prices
        })
        
        # Adicionar candlesticks
        self.fig.add_trace(go.Candlestick(
            x=df['time'],
            open=df['open'],
            high=df['high'],
            low=df['low'],
            close=df['close'],
            name='Preço',
            increasing=dict(
                line=dict(color='#26A69A', width=1),
                fillcolor='#26A69A',
                line_width=1,
            ),
            decreasing=dict(
                line=dict(color='#EF5350', width=1),
                fillcolor='#EF5350',
                line_width=1,
            ),
            whiskerwidth=1,
            showlegend=True
        ))
        
        # Adicionar médias móveis
        self.fig.add_trace(go.Scatter(
            x=self.times,
            y=self.ma_short,
            mode='lines',
            name=f'Média Curta ({self.max_points})',
            line=dict(color='#F5D300', width=1.5)
        ))
        
        self.fig.add_trace(go.Scatter(
            x=self.times,
            y=self.ma_long,
            mode='lines',
            name=f'Média Longa ({self.max_points})',
            line=dict(color='#2962FF', width=1.5)
        ))
        
        # Adicionar stop loss e take profit se estiver em posição
        if self.in_position and self.stop_loss is not None:
            self.fig.add_trace(go.Scatter(
                x=self.times,
                y=[self.stop_loss] * len(self.times),
                mode='lines',
                name='Stop Loss',
                line=dict(color='#880000', width=1, dash='dash'),
                showlegend=True
            ))
            
        if self.in_position and self.take_profit is not None:
            self.fig.add_trace(go.Scatter(
                x=self.times,
                y=[self.take_profit] * len(self.times),
                mode='lines',
                name='Take Profit',
                line=dict(color='#008888', width=1, dash='dash'),
                showlegend=True
            ))
        
        # Adicionar marcadores de compra e venda
        if len(self.buy_points_x) > 0:
            self.fig.add_trace(go.Scatter(
                x=self.buy_points_x,
                y=self.buy_points_y,
                mode='markers',
                name='Compra',
                marker=dict(
                    symbol='triangle-up',
                    size=16,
                    color='#26A69A',
                    line=dict(width=2, color='white')
                ),
                showlegend=True
            ))
        
        if len(self.sell_points_x) > 0:
            self.fig.add_trace(go.Scatter(
                x=self.sell_points_x,
                y=self.sell_points_y,
                mode='markers',
                name='Venda',
                marker=dict(
                    symbol='triangle-down',
                    size=16,
                    color='#EF5350',
                    line=dict(width=2, color='white')
                ),
                showlegend=True
            ))
        
        # Salvar gráfico
        self.save_chart()

    def add_buy_point(self, price):
        """Adiciona um ponto de compra no gráfico"""
        current_index = len(self.close_prices) - 1
        self.buy_points_x.append(self.times[current_index])
        self.buy_points_y.append(float(price))
        self.in_position = True
        
        # Atualizar gráfico imediatamente
        self.update_data(
            current_price=self.close_prices[-1],
            ma_short=self.ma_short[-1],
            ma_long=self.ma_long[-1],
            open_price=self.open_prices[-1],
            high_price=self.high_prices[-1],
            low_price=self.low_prices[-1],
            stop_loss=None,
            take_profit=None
        )

    def add_sell_point(self, price):
        """Adiciona um ponto de venda no gráfico"""
        current_index = len(self.close_prices) - 1
        self.sell_points_x.append(self.times[current_index])
        self.sell_points_y.append(float(price))
        self.in_position = False
        
        # Atualizar gráfico imediatamente
        self.update_data(
            current_price=self.close_prices[-1],
            ma_short=self.ma_short[-1],
            ma_long=self.ma_long[-1],
            open_price=self.open_prices[-1],
            high_price=self.high_prices[-1],
            low_price=self.low_prices[-1],
            stop_loss=None,
            take_profit=None
        )

    def save_chart(self):
        """Salva o gráfico em HTML"""
        config = {
            'displayModeBar': True,
            'scrollZoom': True,
            'modeBarButtonsToAdd': ['drawline', 'eraseshape'],
            'responsive': True,
            'displaylogo': False,
            'toImageButtonOptions': {
                'format': 'png',
                'filename': 'chart',
                'height': 800,
                'width': 1200,
                'scale': 2
            }
        }
        
        self.fig.write_html(
            self.chart_file,
            include_plotlyjs=True,
            full_html=True,
            auto_open=False,
            config=config,
            include_mathjax=False,
            validate=True,
            default_width='100%',
            default_height='100%'
        ) 