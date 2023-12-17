import json
import openai
import pandas 
import streamlit as st
import matplotlib.pyplot as plt
import yfinance as yf

openai.api_key = open('API_KEY.txt', 'r').read()

def get_stock_price(ticker):
    return str(yf.Ticker(ticker).history(period='1y').iloc[-1].Close)

def calculate_SMA(ticker, window):
    data = yf.Ticker(ticker).history(period='1y').Close
    return str(data.ewm(span=window, adjust=False).mean().iloc[-1])

def calculate_EMA(ticker, window):
    data = yf.Ticker(ticker).history(period='1y').Close
    return str(data.rolling(window=window).mean().iloc[-1])

def calculate_RSI(ticker):
    data = yf.Ticker(ticker).history(period='1y').Close
    delta = data.diff()
    up = delta.clip(lower=0)
    down = -1*delta.clip(upper=0)
    ema_up = up.ewm(com=13, adjust=False).mean()
    ema_down = down.ewm(com=13, adjust=False).mean()
    rs = ema_up/ema_down
    return str(100 - (100/(1+rs.iloc[-1])))

def calculate_MACD(ticker):
    data = yf.Ticker(ticker).history(period='1y').Close
    short_EMA = data.ewm(span=12, adjust=False).mean()
    long_EMA = data.ewm(span=26, adjust=False).mean()
    MACD = short_EMA - long_EMA
    signal = MACD.ewm(span=9, adjust=False).mean()
    MACD_histogram = MACD - signal

    return f'{MACD[-1]}, {signal[-1]}, {MACD_histogram[-1]}'

def plot_stock_price(ticker):
    data = yf.Ticker(ticker).history(period='1y')
    plt.figure(figsize=(10, 5))
    plt.plot(data.index, data.Close)
    plt.title(f'{ticker} Stock Price over the last year')
    plt.xlabel('Date')
    plt.ylabel('Price ($)')
    plt.grid(True)
    plt.savefig('stock.jpg')
    plt.close()

functions = [
    {
        'name': 'Get Stock Price',
        'description': 'Get the current stock price of a company',
        'parameters': {
            'type':'object',
            'properties': {
                'ticker': {
                    'type': 'string',
                    'description': 'The stock ticker symbol for the company(for example, AAPL for Apple)'
                }
            },
            'required': ['ticker']
        }
    },
    {
        "name": "Calculate SMA",
        "description": "Calculate the Simple Moving Average of a stock",
        "parameters": {
            "type": "object",
            "properties": {
                "ticker": {
                    "type": "string",
                    "description": "The stock ticker symbol for the company(for example, AAPL for Apple)"
                },
                "window": {
                    "type": "integer",
                    "description": "The timeframe to consider for the SMA calculation"
                }
            },
            "required": ["ticker", "window"]
        },
    },
    {
        "name": "Calculate EMA",
        "description": "Calculate the Exponential Moving Average of a stock",
        "parameters": {
            "type": "object",
            "properties": {
                "ticker": {
                    "type": "string",
                    "description": "The stock ticker symbol for the company(for example, AAPL for Apple)"
                },
                "window": {
                    "type": "integer",
                    "description": "The timeframe to consider for the EMA calculation"
                }
            },
            "required": ["ticker", "window"]
        },
    },
    {
        "name": "Calculate RSI",
        "description": "Calculate the Relative Strength Index of a stock",
        "parameters": {
            "type": "object",
            "properties": {
                "ticker": {
                    "type": "string",
                    "description": "The stock ticker symbol for the company(for example, AAPL for Apple)"
                }
            },
            "required": ["ticker"]
        },
    },
    {
        "name": "Calculate MACD",
        "description": "Calculate the Moving Average Convergence Divergence of a stock",
        "parameters": {
            "type": "object",
            "properties": {
                "ticker": {
                    "type": "string",
                    "description": "The stock ticker symbol for the company(for example, AAPL for Apple)"
                }
            },
            "required": ["ticker"]
        },
    },
    {
        "name": "Plot Stock Price",
        "description": "Plot the stock price of a company over the last year",
        "parameters": {
            "type": "object",
            "properties": {
                "ticker": {
                    "type": "string",
                    "description": "The stock ticker symbol for the company(for example, AAPL for Apple)"
                }
            },
            "required": ["ticker"]
        },
    },
]    

available_functions ={
    'Get Stock Price': get_stock_price,
    'Calculate SMA': calculate_SMA,
    'Calculate EMA': calculate_EMA,
    'Calculate RSI': calculate_RSI,
    'Calculate MACD': calculate_MACD,
    'Plot Stock Price': plot_stock_price
}

if 'messages' not in st.session_state:
    st.session_state['messages'] =[]

st.title('Stock-Bot Assistant')

user_input = st.text_input('Your input:')

if user_input:
    try:
        st.session_state['messages'].append({'user': user_input})
        response = openai.Completion.create(
            model= 'gpt-3.5-turbo-0613',
            messages= st.session_state['messages'],
            functions = functions,
            function_call ='auto'
        )

        response_message = response['choices'][0]['message']

        if response_message.get('function_call'):
            function_name = response_message['function_call']['name']
            function_args = json.loads(response_message['function_call']['arguments'])
            if function_name in ['get_stock_price','calculate_RSI', 'calculate_MACD', 'plot_stock_price']:
                args_dict = {'ticker': function_args.get('ticker')}
            elif function_name in ['calculate_SMA', 'calculate_EMA']:
                args_dict = {'ticker': function_args.get('ticker'), 'window': function_args.get('window')}
            
            function_to_call = available_functions[function_name]
            function_response = function_to_call(**args_dict)

            if function_name == 'plot_stock_price':
                st.image('stock.jpg')
            else:
                st.session_state['messages'].append(response_message)
                st.session_state['messages'].append(
                    {
                        'role': 'function',
                        'name': function_name,
                        'content': function_response
                    }
                )

                second_response = openai.Completion.create(
                    model= 'gpt-3.5-turbo-0613',
                    messages= st.session_state['messages']
                )
                st.text(second_response['choices'][0]['message']['content'])
                st.session_state['messages'].append({'role': 'assistant', 'content': second_response['choices'][0]['message']['content']})
        else:
            st.text(response_message['content'])
            st.session_state['messages'].append({'role': 'assistant', 'content': response_message['content']})
    except Exception as e:
        st.text('Error: ' + str(e))
                    

                
