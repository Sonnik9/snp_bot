import time
from datetime import datetime
import hmac
import json
import requests
import base64
from hashlib import sha256
from urllib.parse import urlencode
import pytz
from log import Total_Logger
import inspect

file_path = 'settings.json'

class TradingParams:
    def __init__(self):
        self.file_path = file_path
        self.load_params()

    def load_params(self):
        # Загрузка и проверка параметров
        with open(self.file_path, 'r', encoding='utf-8') as file:
            data = json.load(file)

            required_keys = [
                'my_name', 'market_place_list', 'market_place_number',
                'symbol', 'tz_location_str', 'is_sync', 'listing_data_time',
                'start_delay_time_sec', 'buy_params', 'sales_share_ratio', 'keys'
            ]

            missing_keys = [key for key in required_keys if key not in data]
            if missing_keys:
                raise ValueError(f"Отсутствуют ключи в настройках: {', '.join(missing_keys)}")

            # Присваивание параметров после проверки
            self.__dict__.update(data)
            self.tz_location = pytz.timezone(self.tz_location_str)

    def display_params(self):
        # Отображение основных параметров
        print(f"\nName: {self.my_name}")
        print(f"Selected Market Place: {self.market_place_list[self.market_place_number - 1]}")
        print(f"Symbol: {self.symbol}")
        print(f"Time Zone: {self.tz_location_str}")
        print(f"Is Sync: {self.is_sync}")
        print(f"Listing Time: {self.listing_data_time}")
        print(f"Start Delay (sec): {self.start_delay_time_sec}\n")

        # Обработка и вывод buy_params
        buy_params_output = '\n\n'.join(
            f"Buy Param #{i + 1}\n" + '\n'.join(f"{k}: {v}" for k, v in param.items())
            for i, param in enumerate(self.buy_params)
        )
        print(f"Buy Params:\n{buy_params_output}\n")

        # Обработка и вывод sales_share_ratio
        sell_params_output = '\n\n'.join(
            f"Sell Params #{i + 1}\n" + '\n'.join(f"{k}: {v}" for k, v in param.items())
            for i, param in enumerate(self.sales_share_ratio)
        )
        print(f"Sell Params:\n{sell_params_output}\n")

        # # Вывод ключей API
        # print(f"API Keys: {self.keys}\n")

# Класс для работы с API бирж
class ORDERS_API(Total_Logger, TradingParams):
    def __init__(self):
        super().__init__()
        # Загрузка API ключей
        self.binance_api_public_key = self.keys.get('BINANCE_API_PUBLIC_KEY')
        self.binance_api_private_key = self.keys.get('BINANCE_API_PRIVATE_KEY')

        self.bitget_api_public_key = self.keys.get('BITGET_API_PUBLIC_KEY')
        self.bitget_api_private_key = self.keys.get('BITGET_API_PRIVATE_KEY')
        self.bitget_api_passphrase = self.keys.get('BITGET_API_PASSPHRASE')

        self.okx_api_public_key = self.keys.get('OKX_API_PUBLIC_KEY')
        self.okx_api_private_key = self.keys.get('OKX_API_PRIVATE_KEY')
        self.okx_api_passphrase = self.keys.get('OKX_API_PASSPHRASE')

        self.orders_url_binance = "https://api.binance.com/api/v3/order"
        self.base_url_bitget = "https://api.bitget.com"
        self.orders_endpoint_bitget = "/api/v2/spot/trade/place-order"
        self.orders_url_bitget = self.base_url_bitget + self.orders_endpoint_bitget
        self.order_data_endpoint = "/api/v2/spot/trade/orderInfo"
        self.okx_base_url = "https://www.okx.com"
        self.okx_order_endpoint = "/api/v5/trade/order"

        self.binance_headers = {
            'X-MBX-APIKEY': self.binance_api_public_key
        }

        self.bitget_headers = {
            "ACCESS-KEY": self.bitget_api_public_key,
            "ACCESS-SIGN": "",
            "ACCESS-TIMESTAMP": "",
            "ACCESS-PASSPHRASE": self.bitget_api_passphrase,
            "Content-Type": "application/json",
            "locale": "en-US"
        }

        self.okx_headers = {
            'OK-ACCESS-KEY': self.okx_api_public_key,
            'OK-ACCESS-PASSPHRASE': self.okx_api_passphrase,
            'Content-Type': 'application/json'
        }

        self.replace_symbol_dict = {
            "USDT": "-USDT", "FUSD": "-FUSD", "BUSD": "-BUSD",
            "DAI": "-DAI", "TUSD": "-TUSD", "USDC": "-USDC",
            "PAX": "-PAX", "GUSD": "-GUSD", "UST": "-UST", "sUSD": "-sUSD"
        }
        # Декорируем методы с requests_connector
        methods_to_wrap = [
            method_name for method_name, _ in inspect.getmembers(self, predicate=inspect.ismethod)
            if not method_name.startswith("__")  # Исключаем специальные методы
        ]
        for method_name in methods_to_wrap:
            setattr(self, method_name, self.log_exceptions_decorator(getattr(self, method_name)))

        self.session = None
        self.cookies = None

    def init_session(self):
        self.session = requests.Session()

    def updating_session(self, response):
        # print("Fake request session was sending!")         
        self.cookies = response.cookies
        self.session.cookies.update(self.cookies)

    def requests_error_logger(self, resp, is_fake):
        if resp.status_code != 200 and not is_fake:
            print(f"Ошибка ордера: {resp.json()}")
            print(f"Статус код: {resp.status_code}")
        return resp

    # for binance//////
    def place_binance_market_order(self, symbol, size, side, quoteType, is_fake):
        def get_query_str_binance():
            timestamp = int(time.time() * 1000)     
            qty_var = 'quoteOrderQty' if quoteType == 'd' else 'quantity'        
            query_string = f"symbol={symbol}&side={side}&type=MARKET&{qty_var}={size}&timestamp={timestamp}"
            signature = hmac.new(self.binance_api_private_key.encode('utf-8'), query_string.encode('utf-8'), sha256).hexdigest()
            return f"{self.orders_url_binance}?{query_string}&signature={signature}"        
        url = get_query_str_binance()       
        resp = self.session.post(url, headers=self.binance_headers)
        return self.requests_error_logger(resp, is_fake)
    
    # for bitget///////////////
    def place_bitget_market_order(self, symbol, size, side, is_fake):
        timestamp = str(int(time.time() * 1000))
        self.bitget_headers["ACCESS-TIMESTAMP"] = timestamp
        payload = {
            "symbol": symbol,
            "side": side,
            "orderType": 'MARKET',
            "size": str(size)
        }
        payload = {str(key): value for key, value in payload.items()}
        def generate_signature_bitget(timestamp, endpoint, payload):
            message = timestamp + 'POST' + endpoint + json.dumps(payload)
            signature = base64.b64encode(hmac.new(self.bitget_api_private_key.encode('utf-8'), message.encode('utf-8'), sha256).digest())
            return signature
        self.bitget_headers["ACCESS-SIGN"] = generate_signature_bitget(timestamp, self.orders_endpoint_bitget, payload)        
        resp = self.session.post(self.orders_url_bitget, headers=self.bitget_headers, json=payload)
        return self.requests_error_logger(resp, is_fake)
    
    # for okx//////////
    def place_okx_market_order(self, symbol, side, size, is_fake):
        """Отправка рыночного ордера на OKX."""

        def generate_okx_signature(timestamp, method, endpoint, body):
            """Генерация подписи для OKX API."""
            message = f"{timestamp}{method}{endpoint}{body}"
            signature = hmac.new(
                self.okx_api_private_key.encode('utf-8'),
                message.encode('utf-8'),
                sha256
            ).digest()
            return base64.b64encode(signature).decode('utf-8')

        # Генерация таймштампа в формате ISO-8601
        timestamp = datetime.utcnow().isoformat(timespec='milliseconds') + 'Z'
        
        # Замена символа на нужный формат
        for key, val in self.replace_symbol_dict.items():
            if symbol.endswith(key):
                symbol = symbol.replace(key, val)
                break

        payload = {
            "instId": symbol,  # Торговая пара, например BTC-USDT
            "tdMode": "cash",  # Наличный режим торговли
            "side": side.lower(), # "buy" или "sell"
            "ordType": "market",
            "sz": str(size)    # Размер ордера
        }
        body = json.dumps(payload)

        # Добавление подписи и таймштампа в заголовки
        self.okx_headers["OK-ACCESS-TIMESTAMP"] = timestamp
        self.okx_headers["OK-ACCESS-SIGN"] = generate_okx_signature(
            timestamp, "POST", self.okx_order_endpoint, body
        )

        # Отправка запроса
        url = self.okx_base_url + self.okx_order_endpoint
        resp = self.session.post(url, headers=self.okx_headers, data=body)

        return self.requests_error_logger(resp, is_fake)
    
    #  get req//////////////
    def get_server_time(self, market_place):
        """
        Получает серверное время для заданной торговой площадки.

        :param market_place: Название торговой площадки (например, 'binance', 'bitget', или 'okx').
        :return: Серверное время в миллисекундах или None в случае ошибки.
        """
        try:
            if market_place == 'binance':
                response = requests.get('https://api.binance.com/api/v3/time')
                if response.status_code != 200:
                    print(f"Ошибка при получении времени от Binance: {response.status_code} - {response.text}")
                    return None
                return response.json().get('serverTime', 0)

            elif market_place == 'bitget':
                url = "https://api.bitget.com/api/v2/public/time"
                response = requests.get(url)
                if response.status_code != 200:
                    print(f"Ошибка при получении времени от Bitget: {response.status_code} - {response.text}")
                    return None
                return int(response.json().get("data", {}).get('serverTime', 0))

            elif market_place == 'okx':
                url = "https://www.okx.com/api/v5/public/time"
                response = requests.get(url)
                if response.status_code != 200:
                    print(f"Ошибка при получении времени от OKX: {response.status_code} - {response.text}")
                    return None
                return int(response.json().get("data", [])[0].get('ts', 0))

            else:
                raise ValueError("Unsupported market place")

        except requests.RequestException as e:
            print(f"Ошибка при получении времени от {market_place}: {e}")
            return None
        
    def get_bitget_order_data(self, orderId):
        def sign_order_data_bitget(message, secret_key):
            mac = hmac.new(bytes(secret_key, encoding='utf8'), bytes(message, encoding='utf-8'), digestmod='sha256')
            return base64.b64encode(mac.digest()).decode()

        def pre_hash(timestamp, method, request_path, body):
            return timestamp + method.upper() + request_path + body 
        
        timestamp = str(int(time.time() * 1000))        
        params = {"orderId": orderId}
        request_path = self.order_data_endpoint + '?' + urlencode(sorted(params.items()))
        body = ""
        message = pre_hash(timestamp, "GET", request_path, body)
        signature = sign_order_data_bitget(message, self.bitget_api_private_key)
        self.bitget_headers["ACCESS-SIGN"] = signature
        self.bitget_headers["ACCESS-TIMESTAMP"] = timestamp
        resp = self.session.get(self.base_url_bitget + request_path, headers=self.bitget_headers)

        return self.requests_error_logger(resp, False)
            
    def get_okx_order_data(self, orderId, symbol):
        def sign_order_data_okx(message, secret_key):
            """Generate OKX API signature."""
            mac = hmac.new(bytes(secret_key, encoding='utf8'), 
                        bytes(message, encoding='utf-8'), 
                        digestmod='sha256')
            return base64.b64encode(mac.digest()).decode()

        def pre_hash(timestamp, method, request_path, body):
            """Create the pre-hash string."""
            return f"{timestamp}{method.upper()}{request_path}{body}"

        # Generate timestamp in ISO-8601 format with millisecond precision
        timestamp = datetime.utcnow().isoformat(timespec='milliseconds') + 'Z'
        # Замена символа на нужный формат
        for key, val in self.replace_symbol_dict.items():
            if symbol.endswith(key):
                symbol = symbol.replace(key, val)
                break

        # Prepare request path and parameters
        params = {"ordId": orderId, "instId": symbol}  # Добавляем instId
        request_path = f"/api/v5/trade/order?{urlencode(params)}"
        body = ""  # No body needed for GET request

        # Create the message for signing
        message = pre_hash(timestamp, "GET", request_path, body)
        
        # Generate signature
        signature = sign_order_data_okx(message, self.okx_api_private_key)

        # Update headers with the required signature and timestamp
        self.okx_headers["OK-ACCESS-SIGN"] = signature
        self.okx_headers["OK-ACCESS-TIMESTAMP"] = timestamp

        # Make the API request to OKX
        url = self.okx_base_url + request_path
        resp = self.session.get(url, headers=self.okx_headers)

        # Handle and log any potential errors
        return self.requests_error_logger(resp, False)


    def place_market_order(self, market_place, symbol, size, side, is_fake, quoteType):  
        # print(market_place, symbol, size, quoteType, side)
        """Обобщенная функция для размещения ордеров на разных биржах."""
        resp = None
        if market_place == 'binance':            
            resp = self.place_binance_market_order(symbol, size, side, quoteType, is_fake)
        elif market_place == 'bitget':
            resp = self.place_bitget_market_order(symbol, size, side, is_fake)        
        elif market_place == 'okx':
            resp = self.place_okx_market_order(symbol, side, size, is_fake)
        else:
            print(f"Биржа {market_place} не поддерживается.")
        if is_fake:
            self.updating_session(resp)
        return resp