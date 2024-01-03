import PySimpleGUI as sg
from breeze_connect import BreezeConnect
import pandas as pd
from os import path
from time import localtime, asctime
from dateutil.parser import parse
from datetime import date, datetime

#! For testing only, in live, default value must be False
bool_connected = False 
bool_order_validity = False
bool_limits_found = False

def validate_order_json(dict_order):
    dt_expiry = parse(dict_order['expiry_date'])
    if dict_order['product'].lower() in ['options', 'futures'] and isinstance(dt_expiry, date) != True:
        return 'Date time format of expiry date not valid.'
    elif dict_order['order_type'].lower() == 'limit' and dict_order['price'].isnumeric() != True:
        return 'Non-numeric or missing price for limit order.'
    elif dict_order['quantity'].isnumeric() != True:
        return 'Size is not a number.'
    elif dict_order['stock_code'].isascii() != True:
        return 'Symbol is not ASCII.'
    elif dict_order['exchange_code'].lower() not in ['nse', 'nfo', 'bse', 'bso', 'mcx']:
        return 'Exchange not known.'
    elif dict_order['product'].lower() in ['options', 'futures'] and dict_order['exchange_code'].lower() not in ['nfo', 'bso', 'mcx']:
        return 'Futures and options can only be traded in NFO, BSO, or MCX.'
    elif dict_order['product'].lower() not in ['cash', 'futures', 'options']:
        return 'Product can only be cash, futures, or options.'
    elif dict_order['action'].lower() not in ['buy', 'sell']:
        return 'Action can only be buy or sell.'
    elif dict_order['validity'].lower() not in ['ioc', 'day']:
        return 'Validity can only be day or ioc.'
    elif dict_order['strike_price'].isnumeric() != True:
        return 'Strike is not numeric. Check for extra spaces before or after price.'
    elif dict_order['product'].lower() == 'options' and dict_order['right'].lower() not in ['call', 'put', '']:
        return 'Option right can only be call, put, or empty. Spaces not allowed.'
    elif dict_order['order_type'].lower() not in ['market', 'limit']:
        return 'Order type can only be market or limit.'
    else:
        return True

class FromFile():
    def __init__(self, str_location):
        self.str_location = str_location
    
    def get_limits(self):
        try:
            df_freeze_limits = pd.read_excel(self.str_location, engine='xlrd')
            df_freeze_limits = df_freeze_limits.rename(columns=lambda x: x.strip())
            dict_fl = dict(zip(df_freeze_limits.SYMBOL, df_freeze_limits.VOL_FRZ_QTY))
            dict_fl = {k.strip():v for (k,v) in dict_fl.items()}
            return dict_fl
        except Exception as e:
            print(e)
            return False
    
    def calc_limit_qty(dict_fl, str_symbol):
        int_limit_qty = dict_fl.get(str_symbol)
        return int_limit_qty


# from: https://nsearchives.nseindia.com/products/resources/download/qtyfreeze.xls
str_freeze_limits = 'C:\\Users\\Admin\\Documents\\Python Scripts\\pysimpletrader\\qtyfreeze.xls'
try:
    df_freeze_limits = pd.read_excel(str_freeze_limits)
    df_freeze_limits = df_freeze_limits.rename(columns=lambda x: x.strip())
    dict_fl = dict(zip(df_freeze_limits.SYMBOL, df_freeze_limits.VOL_FRZ_QTY)) #pd.Series(df_freeze_limits.SYMBOL.values,index=df_freeze_limits.VOL_FRZ_QTY).to_dict()
    dict_fl = {k.strip():v for (k,v) in dict_fl.items()}
    list_symbols = list(dict_fl.keys())
except Exception as e:
    print(e)
    print('Check location of **qtyfreeze.xls and click refresh.')
    #in case file can't be found, instantiate blanks so that the rest of the program doesn't crash
    dict_fl={}
    list_symbols=[]

tab1_layout =  [[sg.Text('APP KEY'), sg.InputText(default_text='', key='APP_KEY')], 
            [sg.Text('SECRET KEY'), sg.InputText(default_text='',key='SECRET_KEY')],
            [sg.Text('SESSION ID'), sg.InputText(default_text='', key='SESSION_ID')],
            [sg.Button('CONNECT'), sg.Button('DISCONNECT')]
            ]

tab2_layout = [ [sg.Text('List of underlying and their Freeze Quantity Limits')],
                [sg.Multiline(default_text = dict_fl,size=(80,20), key='LIST_LIMITS')],
                [sg.Text('----------------------------------')],
                [sg.Text('Current location of file:'), sg.Input(default_text=str_freeze_limits, key='FILE_LOCATION'), sg.Button(button_text='Read File', key='READ_FILE')]
                #,[sg.Text('File last updated:'), sg.Input(default_text=asctime(localtime(path.getmtime(str_freeze_limits))), disabled=True, key='UPDATED_TIME'), sg.Button(button_text='Refresh', key='UPDATE_LIMITS')]
                ]

tab3_layout = [[sg.Text('Symbol: '), sg.DropDown(values=list_symbols, size=(20,40), key='ORDER_SYMBOL')],
                [sg.Text('Exchange: '), sg.DropDown(values=['NSE', 'NFO', 'BSE', 'BSO', 'MCX'], key='ORDER_EXCHANGE')],
                [sg.Text('Product: '), sg.DropDown(values=['CASH', 'FUTURES', 'OPTIONS'], key='ORDER_PRODUCT')],
                [sg.Text('Action: '), sg.DropDown(values=['BUY', 'SELL'], key='ORDER_ACTION')],
                [sg.Text('Validity: '), sg.DropDown(values=['DAY', 'IOC'], key='ORDER_VALIDITY')],
                [sg.Text('Expiry Date: '), sg.Input(default_text='', key='ORDER_EXPIRY_DATE'), sg.CalendarButton(button_text='Pick Date', target='ORDER_EXPIRY_DATE')],
                [sg.Text('Strike: '), sg.Input(default_text='0', key='ORDER_STRIKE')],
                [sg.Text('Right: '), sg.DropDown(values=['CALL', 'PUT'], key='ORDER_RIGHT')],
                [sg.Text('Order Type: '), sg.DropDown(values=['MARKET', 'LIMIT'], key='ORDER_TYPE')],
                [sg.Text('Price: '), sg.Input(default_text='0', key='ORDER_PRICE')],
                [sg.Text('Size: '), sg.Input(default_text='0', key='ORDER_SIZE')],
               [sg.Button(button_text='PLACE ORDER', key='PLACE_ORDER')]                
             ]

layout = [[sg.TabGroup([[sg.Tab('Connect', tab1_layout), sg.Tab('Reference', tab2_layout), sg.Tab('Order', tab3_layout)]])],
              [sg.Output(size=(80, 20), key='OUTVIEW')] ,
              [sg.Button(button_text='Clear Output', key='CLEAR_OUTPUT')],
              [sg.Button('Close')]]

window = sg.Window('Breeze Order Slicer', layout)
# Event Loop to process "events" and get the "values" of the inputs
while True:
    event, values = window.read()
    if event == sg.WIN_CLOSED or event == 'Close': # if user closes window or clicks cancel
        break

    if event == 'CONNECT':
        print('wait.')
        try:
            breeze = BreezeConnect(api_key=values['APP_KEY'])
            breeze.generate_session(api_secret=values['SECRET_KEY'], session_token=values['SESSION_ID'])
            print("connected.")
            bool_connected=True
        except Exception as e:
            print(type(e))
            print(e.args)
    
    if event == 'UPDATE_LIMITS':
        #code to update limits file from NSEINDIA.COM
        pass

    if event == 'PLACE_ORDER':
        if bool_connected==True and bool_limits_found==True:
            try:
                dict_order = {  'exchange_code':values['ORDER_EXCHANGE'], 
                                'stock_code':values['ORDER_SYMBOL'], 
                                'product':values['ORDER_PRODUCT'], 
                                'action':values['ORDER_ACTION'],
                                'stoploss':'',
                                'validity':values['ORDER_VALIDITY'], 
                                'validity_date':datetime.today().isoformat(),
                                'disclosed_quantity':'0',
                                'expiry_date':parse(values['ORDER_EXPIRY_DATE']).isoformat(), 
                                'strike_price':values['ORDER_STRIKE'], 
                                'right':values['ORDER_RIGHT'], 
                                'order_type':values['ORDER_TYPE'], 
                                'price':values['ORDER_PRICE'],
                                'quantity':values['ORDER_SIZE']
                                }
                bool_order_validity = validate_order_json(dict_order)
            except Exception as e:
                print(e)
                print('Values could not be read from application. Make sure all values are correctly filled.')
            if bool_order_validity != True:
                print(bool_order_validity)
                print('Values could not be read from application. Make sure all values are correctly filled.')
            else:
                try:
                    int_limit_qty = int(dict_fl.get(values['ORDER_SYMBOL']))
                except:
                    print("Symbol not found. Make sure the CSV is up to date.")
                int_size = int(dict_order['quantity'])
                int_order_number = 1
                while (int_size>0):
                    if int_size > int_limit_qty:
                        dict_order['quantity'] = str(int_limit_qty)
                        print('Time: {}, Order number: {}, Order: {}'.format(datetime.now().isoformat(), int_order_number, dict_order))
                        order_response = breeze.place_order(**dict_order)
                        print('\nTime: {}, ****{}****\n'.format(datetime.now().isoformat(), order_response))
                    if int_size < int_limit_qty:
                        dict_order['quantity'] = str(int_size)
                        print('Time: {}, Order number: {}, Order: {}'.format(datetime.now().isoformat(), int_order_number, dict_order))
                        order_response = breeze.place_order(**dict_order)
                        print('\nTime: {}, ****{}****\n'.format(datetime.now().isoformat(), order_response))
                    int_size-=int_limit_qty
                    int_order_number+=1
                    print('remaining quantity = {}'.format(int_size))
        else:
            print('**** NOT CONNECTED or LIMITS NOT LOADED. USE FIRST TWO TABS TO COMPLETE PREREQUISITES. ****')
    if event=='CLEAR_OUTPUT':
        window['OUTVIEW'].Update('')
    if event=='READ_FILE':
        str_freeze_limits = values['FILE_LOCATION']
        try:
            objFile = FromFile(str_freeze_limits)
            dict_fl = objFile.get_limits()
            window['LIST_LIMITS'].Update(dict_fl)
            list_symbols = list(dict_fl.keys())
            window['ORDER_SYMBOL'].Update(values=list_symbols)
            print('Quantity Freeze Limits updated. Ready to place order.')
            bool_limits_found = True
        except Exception as e:
            print("File read failed, check location and content: {}".format(e))
        
        # try:
        #     df_freeze_limits = pd.read_excel(str_freeze_limits)
        #     df_freeze_limits = df_freeze_limits.rename(columns=lambda x: x.strip())
        #     dict_fl = dict(zip(df_freeze_limits.SYMBOL, df_freeze_limits.VOL_FRZ_QTY)) #pd.Series(df_freeze_limits.SYMBOL.values,index=df_freeze_limits.VOL_FRZ_QTY).to_dict()
        #     dict_fl = {k.strip():v for (k,v) in dict_fl.items()}
        #     list_symbols = list(dict_fl.keys())
        #     values['LIST_LIMITS'].update(dict_fl)
        #     values['ORDER_SYMBOL'].update(list_symbols)
        # except Exception as e:
        #     print(e)
        #     print('Check location of **qtyfreeze.xls and click refresh.')
        #     #in case file can't be found, instantiate blanks so that the rest of the program doesn't crash
        #     dict_fl={}
        #     list_symbols=[]
        
window.close()
