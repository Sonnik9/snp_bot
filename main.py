import time
import random
from datetime import datetime
import sys
from api_orders import ORDERS_API
from decimal import Decimal, getcontext, ROUND_DOWN
import pytz
import os
import inspect

current_file = os.path.basename(__file__)
getcontext().prec = 12  # Установите необходимую вам точность вычислений

def gen_bible_quote():
    random_bible_list = [
        "<<Благодать Господа нашего Иисуса Христа, и любовь Бога Отца, и общение Святаго Духа со всеми вами. Аминь.>>\n___(2-е Коринфянам 13:13)___",
        "<<Притом знаем, что любящим Бога, призванным по Его изволению, все содействует ко благу.>>\n___(Римлянам 8:28)___",
        "<<Спокойно ложусь я и сплю, ибо Ты, Господи, един даешь мне жить в безопасности.>>\n___(Пс 4:9)___"
    ]
    
    current_hour = datetime.now().hour
    if 6 <= current_hour < 12:
        return random_bible_list[0]
    elif 12 <= current_hour < 23:
        return random_bible_list[1]
    return random_bible_list[2]

class UTILS(ORDERS_API):
    def __init__(self):
        super().__init__()      
        
        # Декорируем методы с requests_connector
        methods_to_wrap = [
            method_name for method_name, _ in inspect.getmembers(self, predicate=inspect.ismethod)
            if not method_name.startswith("__")  # Исключаем специальные методы
        ]
        for method_name in methods_to_wrap:
            setattr(self, method_name, self.log_exceptions_decorator(getattr(self, method_name)))

    def greeting_template(self):
        print(f"{self.my_name}, приветствую тебя!!\n{gen_bible_quote()}")

    def datetime_to_milliseconds(self, datetime_str):
        dt_obj = datetime.strptime(datetime_str, "%Y-%m-%d %H:%M:%S")
        dt_obj = self.tz_location.localize(dt_obj)
        return int(dt_obj.timestamp() * 1000)
    
    def get_date_time_now(self):
        now = datetime.now(self.tz_location)
        return now.strftime("%Y-%m-%d %H:%M:%S")

    def milliseconds_to_datetime(self, milliseconds):
        seconds = milliseconds / 1000
        dt = datetime.fromtimestamp(seconds, pytz.utc).astimezone(self.tz_location)
        return dt.strftime("%Y-%m-%d %H:%M:%S") + f".{int(milliseconds % 1000):03d}" 

    def sync_time(self, market_place, num_requests=4):
        time_diffs = []
        wrong_req_counter = 0
        
        for _ in range(num_requests):
            start_time = time.time() * 1000
            server_time = self.get_server_time(market_place)
            
            if isinstance(server_time, (int, float)):
                end_time = time.time() * 1000
                request_duration = end_time - start_time
                time_diff = server_time - (start_time + request_duration / 2)
                time_diffs.append(time_diff)
                time.sleep(random.uniform(0.7, 1.4))
            else:
                wrong_req_counter += 1
                
        valid_time_diff_count = len(time_diffs)
        
        # Возвращаем среднее временное смещение, если есть действительные значения
        if valid_time_diff_count > 0:
            return sum(time_diffs) / valid_time_diff_count
        else:
            return 0       

    def wait_until(self, listing_time_ms, buffer_time_ms=60000):
        """Ждёт до указанного времени с учётом буфера."""
        current_time_ms = int(time.time() * 1000)
        left_time_sec = (listing_time_ms - buffer_time_ms - current_time_ms) / 1000

        if left_time_sec <= 0:
            print('Текущее время больше чем время старта')
            return False

        print(f"Осталось до старта: {round((left_time_sec + buffer_time_ms / 1000) / 60, 3)} мин\n")
        time.sleep(left_time_sec)
        return True

    def start_order_process(self, market_place):
        """Основной процесс отправки ордеров с учётом задержки."""
        # Ждём до первого этапа
        time_offset = 0
        print(f"Время: {self.get_date_time_now()}")
        listing_time_ms = self.datetime_to_milliseconds(self.listing_data_time)
        if not self.wait_until(listing_time_ms):
            return False
        
        try:
            # Инициализация сессии и тестовый запрос
            self.init_session()
            self.place_market_order(market_place, 'TESTABRAIKABRA', 7, 'BUY', True, 'd')
        except Exception as ex:
            self.handle_messagee("Проблемы при попытке инициализировать тестовый ордер:")
            self.handle_exception(f"{ex} на строке {inspect.currentframe().f_lineno} в файле {current_file}")
        
        # print(f"self.start_delay_time_sec: {self.start_delay_time_sec}")
        # Ждём до начала продажи с учётом задержки
        if self.is_sync:
            self.handle_messagee("Синхронизация времени начата. Немного подождите")
            time_offset = self.sync_time(market_place)
            self.handle_messagee(f"Синхронизация времени окончена. Поправка синхронизации: {time_offset} milliseconds")
        current_time_ms = int(time.time() * 1000)
        left_time_sec = (listing_time_ms + self.start_delay_time_sec * 1000 - current_time_ms - time_offset) / 1000

        if left_time_sec <= 0:
            print('Текущее время больше чем время старта')
            return False

        time.sleep(left_time_sec)
        return True
    
    def process_order_response(self, place_market_order_resp):
        """Проверяет и возвращает данные запроса и статус."""
        if place_market_order_resp is not None:
            try:
                return place_market_order_resp.json(), place_market_order_resp.status_code
            except Exception as ex:
                self.handle_exception(f"{ex} на строке {inspect.currentframe().f_lineno} в файле {current_file}")                
        return None, None
        
    def print_order_data(self, place_market_order_resp_j, status, market_place):
        """Печатает данные ордера или ошибку."""
        if isinstance(place_market_order_resp_j, dict):
            if market_place == 'binance':
                specific_key_list = [
                    "orderId", "status", "symbol", "side", 
                    "executedQty", "cummulativeQuoteQty", "transactTime"
                ]
                order_details = "\n".join(
                    f"{k}: {v}" for k, v in place_market_order_resp_j.items() if k in specific_key_list
                )
                # Время транзакции для Binance
                timestamp = place_market_order_resp_j.get("transactTime")

            elif market_place == 'bitget':
                order_details = "\n".join(f"{k}: {v}" for k, v in place_market_order_resp_j.items())
                # Время транзакции для Bitget
                timestamp = place_market_order_resp_j.get("requestTime")

            elif market_place == 'okx':
                # Извлечение данных и выбор приоритетного времени для OKX
                data_list = place_market_order_resp_j.get('data', [{}])
                data_item = data_list[0] if data_list else {}

                ts = data_item.get('ts')  # Основное время транзакции
                in_time = place_market_order_resp_j.get('inTime')  # Время входа запроса
                out_time = place_market_order_resp_j.get('outTime')  # Время выхода запроса

                # Преобразуем в int при необходимости
                timestamp = next(
                    (int(t) for t in [ts, in_time, out_time] if t and isinstance(t, (int, str))),
                    None
                )

                order_details = "\n".join(f"{k}: {v}" for k, v in data_item.items())

            # Проверяем и конвертируем timestamp в дату
            if timestamp:
                try:
                    now_time = self.milliseconds_to_datetime(int(timestamp))
                except ValueError:
                    print(f"Неверный формат времени: {timestamp}")
                    now_time = None
            else:
                now_time = None

            # Печать результатов
            print(f'Время транзакции: {now_time}')
            print(f"Данные ордера:\nСтатус ответа: {status}\n{order_details}\n")

        else:
            print(f"Ошибка при создании ордера. Текст ошибки: {status}")

    def _adjust_quantity(self, quantity: Decimal, share_percent: Decimal) -> Decimal:
        """Корректируем количество в зависимости от его значения."""
        adjusted_quantity = (share_percent / Decimal(100)) * quantity

        if quantity >= Decimal(20):
            # Умножаем на 0.99 и округляем вниз для целого значения.
            return (adjusted_quantity * Decimal('0.99')).to_integral_value(rounding=ROUND_DOWN)
        elif Decimal('1') < quantity < Decimal('20'):
            # Округляем до целого вниз.
            return adjusted_quantity.to_integral_value(rounding=ROUND_DOWN)
        else:
            # Для небольших значений оставляем точность до 8 знаков.
            return adjusted_quantity * Decimal('0.99').quantize(Decimal('0.00000001'), rounding=ROUND_DOWN)


    def _calculate_quantity(self, fills, key="qty"):
        """Вспомогательная функция для расчета количества."""
        try:
            return sum(Decimal(fill.get(key, 0)) for fill in fills)
        except Exception as ex:
            self.handle_exception(f"{ex} на строке {inspect.currentframe().f_lineno} в файле {current_file}")
            return 0

    def qty_extracter(self, market_place, response):
        """Извлекает количество и стоимость продажи (в USDT) для указанной биржи."""
        qty = Decimal(0)
        price = Decimal(0)
        usdt_value = Decimal(0)

        try:
            if market_place == 'binance':
                fills = response.get("fills", [])
                qty = self._calculate_quantity(fills, key="qty")
                price = sum(Decimal(fill["price"]) for fill in fills)
                usdt_value = qty * price

            elif market_place == 'bitget':
                bitget_order_id = response.get('data', {}).get('orderId')
                if bitget_order_id is None:
                    self.handle_messagee("Проблемы при попытке получить данные ордера")
                    return 0, 0, 0

                for attempt in range(1, 3):  # Три попытки получить данные
                    get_data_resp = self.get_bitget_order_data(bitget_order_id)
                    get_data_order_data, get_data_status = self.process_order_response(get_data_resp)

                    if get_data_status == 200 and get_data_order_data:
                        fills = get_data_order_data.get("data", [])
                        qty = self._calculate_quantity(fills, key="baseVolume")  # Получаем количество
                        price = sum(Decimal(fill['priceAvg']) for fill in fills)
                        usdt_value = sum(Decimal(fill['quoteVolume']) for fill in fills)  # Прямо из данных берем значение в USDT
                        if qty != 0:
                            break
                    else:
                        self.handle_messagee(f"Проблемы при получении данных ордера. Попытка: {attempt}")
                        time.sleep(0.1)

            elif market_place == 'okx':
                okx_order_id = response.get('data', [{}])[0].get('ordId')
                if okx_order_id is None:
                    self.handle_messagee("Проблемы при попытке получить данные ордера на OKX")
                    return 0, 0, 0

                for attempt in range(1, 3):
                    get_data_resp = self.get_okx_order_data(okx_order_id, self.symbol)
                    get_data_order_data, get_data_status = self.process_order_response(get_data_resp)

                    if get_data_status == 200 and get_data_order_data:
                        # print(get_data_order_data)
                        fills = get_data_order_data.get("data", [])
                        qty = self._calculate_quantity(fills, key="fillSz")  # Получаем количество токенов
                        price = sum(Decimal(fill['fillPx']) for fill in fills)
                        usdt_value = qty * price  # Если есть, взять значение в USDT
                        if qty != 0:
                            break
                    else:
                        self.handle_messagee(f"Проблемы при получении данных ордера на OKX. Попытка: {attempt}")
                        time.sleep(0.1)

            return qty, usdt_value, price

        except Exception as ex:
            self.handle_exception(f"{ex} на строке {inspect.currentframe().f_lineno} в файле {current_file}")
            return 0, 0, 0

    def result_logger(self, place_market_order_resp_list, market_place):
        # Initialize totals and counters
        total_buy_qty = total_buy_usdt = acum_buy_price = Decimal(0)
        total_sell_qty = total_sell_usdt = acum_sell_price = Decimal(0)
        progress_counter_buy = progress_counter_sell = Decimal(0)

        # Process market order responses
        if place_market_order_resp_list:
            for order_data, status, side in place_market_order_resp_list:
                try:
                    self.print_order_data(order_data, status, market_place)
                    qty, usdt_value, price = self.qty_extracter(market_place, order_data)

                    if qty > 0:
                        if side == "BUY":
                            progress_counter_buy += 1
                            total_buy_qty += Decimal(qty)
                            total_buy_usdt += Decimal(usdt_value)
                            acum_buy_price += Decimal(price)
                        elif side == "SELL":
                            progress_counter_sell += 1
                            total_sell_qty += Decimal(qty)
                            total_sell_usdt += Decimal(usdt_value)
                            acum_sell_price += Decimal(price)

                except Exception as ex:
                    self.handle_exception(
                        f"Ошибка: {ex} на строке {inspect.currentframe().f_lineno} в файле {current_file}"
                    )

        # Calculate progress, averages, and profit
        in_plane_buy = sum(1 for x in place_market_order_resp_list if x[2] == "BUY")
        in_plane_sell = sum(1 for x in place_market_order_resp_list if x[2] == "SELL")

        progress_per_buy = (progress_counter_buy * 100 / in_plane_buy) if in_plane_buy else 0
        progress_per_sell = (progress_counter_sell * 100 / in_plane_sell) if in_plane_sell else 0

        average_buy_price = (acum_buy_price / progress_counter_buy) if progress_counter_buy else Decimal(0)
        average_sell_price = (acum_sell_price / progress_counter_sell) if progress_counter_sell else Decimal(0)

        profit_usdt = total_sell_usdt - total_buy_usdt
        profit_per = ((acum_sell_price - acum_buy_price) / acum_buy_price * 100) if acum_buy_price > 0 else Decimal(0)
        left_tokens = total_sell_qty - total_buy_qty

        # Логирование результатов
        self.handle_messagee(
            f"Результаты торгов:\n"
            f"Куплено токенов: {total_buy_qty}, Средняя цена покупки: {average_buy_price}, "
            f"Сумма покупки в USDT: {total_buy_usdt}, Прогресс покупок: {progress_per_buy}%\n"
            f"Продано токенов: {total_sell_qty}, Средняя цена продаж: {average_sell_price}, "
            f"Сумма продаж в USDT: {total_sell_usdt}, Прогресс продаж: {progress_per_sell}%\n"
            f"Профит в USDT: {profit_usdt}\n"
            f"Профит в %: {profit_per}\n"
            f"Осталось токенов: {left_tokens}\n"
        )
        
class MAIN_LOGIC(UTILS):
    def trading_logic_template(self):
        place_market_order_resp_list = []
        if not isinstance(self.market_place_number, int):
            print("Номер биржи выбран неверно")
            return False
        market_place = self.market_place_list[self.market_place_number - 1]

        if self.is_bible_quotes_introdaction:
            self.greeting_template()            
        if not self.start_order_process(market_place):
            return False
                
        # start trading:
        # buy logic:       
        for item in self.buy_params:
            try:
                buy_order_data = None
                buy_status = 0
                size = item.get('size')
                quoteType = item.get('quoteType')
                middle_order_pause = item.get('delay_seconds', 0)  
                buy_market_order_resp = self.place_market_order(market_place, self.symbol, size, "BUY", False, quoteType)
                buy_order_data, buy_status = self.process_order_response(buy_market_order_resp)
                if not buy_order_data or buy_status != 200:
                    self.handle_messagee("Проблемы при попытке создать ордер на покупку")
                    continue
                place_market_order_resp_list.append((buy_order_data, buy_status, "BUY"))
                time.sleep(middle_order_pause)
            except Exception as ex:
                self.handle_messagee("Проблемы при попытке создать ордер на покупку:")
                self.handle_exception(f"{ex} на строке {inspect.currentframe().f_lineno} в файле {current_file}")                
        
        # sell logic:
        if place_market_order_resp_list:
            total_size = Decimal(0)
            for buy_order_data, _, _ in place_market_order_resp_list:
                try:
                    total_item_size, _, _ = self.qty_extracter(market_place, buy_order_data)
                    total_size += total_item_size
                except Exception as ex:
                    self.handle_messagee("Проблемы при попытке извлечь данные о покупке:")
                    self.handle_exception(f"{ex} на строке {inspect.currentframe().f_lineno} в файле {current_file}")
            
            for item in self.sales_share_ratio:
                try:
                    sell_order_data, sell_status = None, 0
                    share_percent, delay_seconds = Decimal(item.get("share_percent")), item.get("delay_seconds")
                    size = self._adjust_quantity(total_size, share_percent)                    
                    place_market_order_resp = self.place_market_order(market_place, self.symbol, size, 'SELL', False, 'q')               
                    sell_order_data, sell_status = self.process_order_response(place_market_order_resp)
                    if not sell_order_data or sell_status != 200:
                        self.handle_messagee("Проблемы при попытке создать ордер на продажу") 
                        continue                   
                    place_market_order_resp_list.append((sell_order_data, sell_status, "SELL"))
                    time.sleep(delay_seconds)
                except Exception as ex:
                    self.handle_messagee("Проблемы при попытке создать ордер на продажу:")
                    self.handle_exception(f"{ex} на строке {inspect.currentframe().f_lineno} в файле {current_file}")

        self.result_logger(place_market_order_resp_list, market_place)
        
        return True
        
def main():
    main_logic_instanse = MAIN_LOGIC()
    print("Инструкция находится в файле README.md. Настройки -- файл settings.json")
    print("Текущие настройки: ")
    main_logic_instanse.display_params()
    print()
    intro_answer = input('Начинаем? (y/n)').strip()
    print()
    if intro_answer == "y":     
        if not main_logic_instanse.trading_logic_template():
            print("Ошибка в работе бота.")
    input('Завершить работу? (Enter)')
    print("Работа программы завершена")
    time.sleep(1)
    sys.exit()    

if __name__ == "__main__":
    main()

# python main.py
# python3 -m venv .venv
# source .venv/bin/activate
# pip install -r requirements.txt

# pip install virtualenv
# virtualenv myenv
# myenv\Scripts\activate.bat
# pip install -r requirements.txt
# pyinstaller --onefile main.py

# pyinstaller --onefile --add-data 'path/to/config.json:.' main.py -- не нужно но для справок
# chmod +x main
# chmod +x ./main
# ./main
