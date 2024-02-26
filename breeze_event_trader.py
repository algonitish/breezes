from breeze_connect import BreezeConnect
from talipp.indicators import EMA
from time import perf_counter

api='7@63mU944915526816n9lk80650Y5110'
secret='8d5527490v99fZ6u399w2^h78862`23N'
session='35342996'

breeze = BreezeConnect(api_key=api)
breeze.generate_session(api_secret=secret,session_token=session)

float_stoploss = 22165.0

# Connect to websocket(it will connect to tick-by-tick data server)
breeze.ws_connect()

int_fast = 9
int_slow = 26
list_hist_fast = []
list_hist_slow = []
list_ema_fast = []
list_ema_slow = []

def crossover(list1: list, list2: list):
    '''
    input: lists l1 and l2
    output: 0 if no crossover, 1 if first list crossed second, -1 if other way around
    '''
    if list1[-1] > list2[-1] and list1[-2] <= list2[-2]:
        return 1
    elif list1[-1] < list2[-1] and list1[-2] >= list2[-2]:
        return -1
    else:
        return 0



def on_ticks(ticks):
    print(ticks)
    if ticks.get('bPrice') != None:
        #handle_stream(ticks)
        pass
    else:
        handle_ohlc(ticks)
    

def handle_stream(ticks):
    pass
    if float(ticks.get('last')) < float_stoploss:
        print('stoploss hit')

def handle_ohlc(ticks):
    t1 = perf_counter()
    int_signal = 0
    float_close = float(ticks.get('close'))
    if len(list_hist_fast) < int_fast:
        list_hist_fast.insert(0,float_close)
        print('fast: populating')
    else:
        list_hist_fast.pop()
        list_hist_fast.insert(0,float_close)
        list_hist_fast.reverse()
        list_ema_fast.append(EMA(period = int_fast, input_values = list_hist_fast)[-1])
        list_hist_fast.reverse()
    
    if len(list_hist_slow) < int_slow:
        list_hist_slow.insert(0,float_close)
        print('slow: populating')
    else:
        list_hist_slow.pop()
        list_hist_slow.insert(0,float_close)
        list_hist_slow.reverse()
        list_ema_slow.append(EMA(period = int_slow, input_values = list_hist_slow)[-1])
        list_hist_slow.reverse()
        
    crossover(list_ema_fast, list_ema_slow)
    print("ohlc time: ", (perf_counter() - t1))
    return int_signal

# Assign the callbacks.
breeze.on_ticks = on_ticks

# start trading by subscribing to stocks feeds: subscribing to exchange ticks activates the stoploss function, subscribing to the OHLC starts the strategy function
breeze.subscribe_feeds(exchange_code="NFO", stock_code="NIFTY", product_type="futures", expiry_date="29-Feb-2024", strike_price="", right="none", get_exchange_quotes=True, get_market_depth=False)
breeze.subscribe_feeds(exchange_code="NFO", stock_code="NIFTY", product_type="futures", expiry_date="29-Feb-2024", strike_price="", right="none", interval='1second')


breeze.unsubscribe_feeds(exchange_code="NFO", stock_code="NIFTY", product_type="futures", expiry_date="29-Feb-2024", strike_price="", right="none", get_exchange_quotes=True, get_market_depth=False)
breeze.unsubscribe_feeds(exchange_code="NFO", stock_code="NIFTY", product_type="futures", expiry_date="29-Feb-2024", strike_price="", right="none", interval='1second')
