import ccxt
import talib
import numpy as np
import time

# Initialize Binance Futures exchange API
exchange = ccxt.binance({
    'apiKey': 'YOUR_API_KEY',
    'secret': 'YOUR_API_SECRET',
    'enableRateLimit': True,
    'options': {
        'defaultType': 'future',
    },
})

# Set parameters
symbol_list = ['BTC/USDT', 'LTC/USDT', 'ETH/USDT', 'DOGE/USDT']
timeframe = '1h'
rsi_length = 14
stoch_k = 14
stoch_d = 3
leverage_min = 20
leverage_max = 25
stop_loss = 0.95  # 5% stop loss
trade_duration_4h = 4 * 60 * 60  # trade duration in seconds
trade_duration_12h = 12 * 60 * 60  # trade duration in seconds
ema_period = 200


# Define function to check for trading opportunity
def check_trade_opportunity():
    for symbol in symbol_list:
        # Fetch OHLCV data from exchange
        ohlcv = exchange.fetch_ohlcv(symbol, timeframe)

        # Extract closing prices and calculate EMA
        close = [x[4] for x in ohlcv]
        ema = talib.EMA(close, timeperiod=ema_period)

        # Calculate RSI and Stochastic indicators
        rsi = talib.RSI(close, timeperiod=rsi_length)
        stoch_k, stoch_d = talib.STOCH(high, low, close, fastk_period=stoch_k, slowk_period=stoch_d, slowd_period=3)

        # Check if RSI is oversold and Stochastic is bullish and current price is above EMA
        if rsi[-1] < 30 and stoch_k[-1] < stoch_d[-1] and stoch_k[-1] < 20 and close[-1] > ema[-1]:
            return symbol, 'long'
        # Check if RSI is overbought and Stochastic is bearish and current price is below EMA
        elif rsi[-1] > 70 and stoch_k[-1] > stoch_d[-1] and stoch_k[-1] > 80 and close[-1] < ema[-1]:
            return symbol, 'short'

    return None, None


# Define function to execute trade
def execute_trade(symbol, duration, direction):
    # Set leverage
    leverage = exchange.fapiPrivate_post_leverage({
        'symbol': symbol,
        'leverage': leverage_max
    })

    # Check account balance
    balance = exchange.fapiPrivate_get_balance()
    usdt_balance = float(balance['USDT']['availableBalance'])

    # Calculate trade size based on available balance
    trade_size = (usdt_balance * leverage_max * 0.1) / exchange.fetch_ticker(symbol)['last']

    # Place market order to buy or sell symbol depending on direction
    if direction == 'long':
        exchange.create_order(
            symbol=symbol,
            type='MARKET',
            side='BUY',
            amount=trade_size,
            params={'stopPrice': stop_loss}
        )
    else:
        exchange.create_order(
            symbol=symbol,
            type='MARKET',
            side='SELL',
            amount=trade_size,
            params={'stopPrice': stop_loss}
        )

    # Sleep for trade duration
    time.sleep(duration)


