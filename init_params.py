import json
import pytz

file_path = 'settings.json'

class TradingParams:
    def __init__(self):
        self.load_params()
        # self.display_params()

    def load_params(self):
        # Загрузка и проверка параметров
        with open(file_path, 'r', encoding='utf-8') as file:
            data = json.load(file)

            required_keys = [
                'my_name', 'market_place_list', 'market_place_number',
                'tz_location_str', 'is_sync', 'sleep_to', 'work_to', 'start_delay_time_sec',
                'buy_params', 'sales_share_ratio', 'is_bible_quotes_introdaction',
                'is_proxy', 'proxy', 'keys'
            ]

            missing_keys = [key for key in required_keys if key not in data]
            if missing_keys:
                raise ValueError(f"Отсутствуют ключи в настройках: {', '.join(missing_keys)}")

            # Присваивание параметров после проверки
            self.__dict__.update(data)
            self.proxy_url = f'socks5://{self.proxy.get("login")}:{self.proxy.get("password")}@{self.proxy.get("adress")}:{self.proxy.get("socks5_port")}'
            self.proxiess = {
                'http': self.proxy_url,
            }
            # self.proxy_url = f'http://{self.proxy.get("login")}:{self.proxy.get("password")}@{self.proxy.get("adress")}:{self.proxy.get("http_port")}'
            # self.proxiess = {
            #     'https': self.proxy_url,
            #     'http': self.proxy_url,            
            # }
            # print(self.proxy_url)
            self.tz_location = pytz.timezone(self.tz_location_str)

    def display_params(self):
        # Отображение основных параметров
        print(f"\nName: {self.my_name}")
        print(f"Selected Market Place: {self.market_place_list[self.market_place_number - 1]}")
        print(f"Time Zone: {self.tz_location_str}")
        print(f"Is Sync: {self.is_sync}")
        print(f"Start Delay (sec): {self.start_delay_time_sec}\n")

        # Обработка и вывод buy_params
        buy_params_output = '\n\n'.join(
            f"Buy Param #{i + 1}\n" + '\n'.join(f"{k}: {v}" for k, v in param.items())
            for i, param in enumerate(self.buy_params)
        )
        print(f"Buy Params:\n{buy_params_output}\n")

        # Обработка и вывод sales_share_ratio
        sell_params_output = '\n\n'.join(
            f"Sell Param #{i + 1}\n" + '\n'.join(f"{k}: {v}" for k, v in param.items())
            for i, param in enumerate(self.sales_share_ratio)
        )
        print(f"Sell Params:\n{sell_params_output}\n")

        # Вывод параметров прокси-сервера
        print("Proxy Settings:")
        for key, value in self.proxy.items():
            print(f"  {key}: {value}")
        
        # # Вывод API ключей
        # print("\nAPI Keys:")
        # for key, value in self.keys.items():
        #     print(f"  {key}: {value}")
