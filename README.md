# 🤖 Donkey Bot - Bot de Trading com Estratégias Adaptativas

Bot de trading desenvolvido para operar na Binance usando estratégias adaptativas baseadas em médias móveis e indicadores técnicos.

## 📊 Estratégias Implementadas

### Estratégia Principal - Cruzamento de Médias Móveis Adaptativo
- **Médias Utilizadas**:
  - Média Curta: 9 períodos
  - Média Longa: 21 períodos

### Sinais de Entrada (Compra)
1. **Confirmação de Tendência**:
   - Média curta cruza a média longa para cima
   - Preço atual acima de ambas as médias
   - Validação da força da tendência

### Sinais de Saída (Venda)
1. **Stop Loss Dinâmico**:
   - Baseado na volatilidade do mercado (ATR)
   - Ajusta-se automaticamente entre 0.5% e 5%
   - Trailing stop que acompanha a subida do preço

2. **Take Profit Dinâmico**:
   - Baseado na força da tendência
   - Ajusta-se entre 1% e 10%
   - Aumenta em tendências fortes

3. **Sinais Técnicos**:
   - Média curta abaixo da média longa
   - Força da tendência muito fraca (< 0.05%)
   - Preço abaixo da média curta

### Gestão de Risco
1. **Volatilidade Adaptativa**:
   - Uso do ATR (Average True Range) para medir volatilidade
   - Stop loss mais largo em mercados voláteis
   - Stop loss mais próximo em mercados estáveis

2. **Força da Tendência**:
   - Cálculo dinâmico da força da tendência
   - Ajuste automático dos alvos de lucro
   - Proteção contra tendências fracas

3. **Trailing Stop**:
   - Stop loss móvel que acompanha o preço
   - Protege lucros em tendências fortes
   - Atualização contínua baseada na volatilidade

## 🛠 Configuração

### Variáveis de Ambiente (.env)
```env
BINANCE_API_KEY=sua_api_key
BINANCE_API_SECRET=sua_api_secret
SYMBOL=BTCUSDT
QUANTITY=0.001
STOP_LOSS_PERCENT=2.0
TAKE_PROFIT_PERCENT=3.0
```

### Instalação
```bash
pip install -r requirements.txt
```

## 🚀 Uso

### Trading ao Vivo
```bash
python run_bot.py
```

### Backtesting
```bash
python run_backtest.py
```

## 📈 Análise de Performance

O bot gera métricas detalhadas de performance incluindo:

1. **Métricas Gerais**:
   - Total de trades
   - Taxa de acerto (Win rate)
   - Trades vencedores/perdedores

2. **Métricas de Lucro/Prejuízo**:
   - Lucro líquido
   - Fator de lucro
   - Lucro médio por trade

3. **Métricas de Risco**:
   - Drawdown máximo
   - Relação risco/retorno
   - Volatilidade da estratégia

4. **Métricas de Tempo**:
   - Tempo em trades
   - Trades por dia
   - Duração média dos trades

## 📊 Visualização

O bot gera gráficos interativos com:
- Candlesticks
- Médias móveis
- Pontos de entrada/saída
- Níveis de stop loss e take profit
- Indicadores técnicos

## 📝 Logs

Sistema de logging detalhado com:
- Registro de todas as operações
- Atualizações de stops
- Métricas de performance
- Alertas e avisos

## ⚠️ Avisos

- Este bot é para fins educacionais
- Opere sempre com capital de risco
- Resultados passados não garantem resultados futuros
- Faça seus próprios testes antes de operar com dinheiro real

## Contribuições

Contribuições são bem-vindas! Sinta-se à vontade para abrir issues ou pull requests. 


## Anotações
 - Atingiu lucro de 11% em um backtest de 3 meses