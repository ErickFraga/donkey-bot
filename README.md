# Bot de Trading de Criptomoedas

Este é um bot de trading automatizado para criptomoedas que utiliza a estratégia de cruzamento de médias móveis para executar operações na Binance.

## Estratégia

O bot utiliza as seguintes regras para trading:

- Médias móveis: curta (8 períodos) e longa (21 períodos)
- Sinal de compra: média curta cruza acima da média longa
- Stop Loss: -2% do preço de entrada
- Take Profit: +3% do preço de entrada
- Trailing Stop: Quando atinge o take profit, atualiza o stop loss e take profit mantendo as mesmas porcentagens

## Requisitos

- Python 3.8+
- Conta na Binance
- Bot do Telegram (para notificações)

## Instalação

1. Clone o repositório:
```bash
git clone https://github.com/seu-usuario/crypto-trading-bot.git
cd crypto-trading-bot
```

2. Instale as dependências:
```bash
pip install -r requirements.txt
```

3. Copie o arquivo .env.example para .env e configure suas variáveis:
```bash
cp .env.example .env
```

4. Configure as seguintes variáveis no arquivo .env:
- BINANCE_API_KEY: Sua API key da Binance
- BINANCE_API_SECRET: Sua API secret da Binance
- TELEGRAM_BOT_TOKEN: Token do seu bot do Telegram
- TELEGRAM_CHAT_ID: ID do chat onde receberá as notificações
- SYMBOL: Par de trading (ex: BTCUSDT)
- QUANTIDADE: Quantidade para operar

## Uso

Para iniciar o bot:
```bash
python main.py
```

## Funcionalidades

- Trading automatizado baseado em médias móveis
- Stop Loss e Take Profit automáticos
- Trailing Stop para maximizar lucros
- Notificações via Telegram
- Registro de ordens em JSON
- Sistema de logs detalhado

## Estrutura do Projeto

```
trading_bot/
├── trading_manager.py  # Gerenciador principal de trading
├── order_manager.py    # Gerenciamento de ordens
├── telegram_notifier.py # Notificações Telegram
└── logger.py           # Sistema de logs

data/
└── orders.json         # Histórico de ordens

logs/
└── trading_bot_*.log   # Arquivos de log

main.py                 # Arquivo principal
requirements.txt        # Dependências
.env                    # Configurações
```

## Avisos

- Este bot é para fins educacionais
- Trading de criptomoedas envolve riscos
- Teste primeiro em uma conta de teste
- Não invista mais do que pode perder

## Contribuições

Contribuições são bem-vindas! Sinta-se à vontade para abrir issues ou pull requests. 