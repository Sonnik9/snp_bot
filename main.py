import time
from datetime import datetime
import sys
from parser import BitgetParser
from decimal import Decimal, getcontext, ROUND_DOWN
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
        
class MAIN_LOGIC(BitgetParser):
    def greeting_template(self):
        print(f"{self.my_name}, приветствую тебя!!\n{gen_bible_quote()}")

    def trading_logic_template(self, market_place, symbol='NOTUSDT', listing_time_ms=int(time.time()* 1000) + 60000):
        place_market_order_resp_list = []
           
        if not self.start_order_process(market_place, listing_time_ms):
            return False

        # buy logic:       
        for item in self.buy_params:
            try:
                buy_order_data = None
                buy_status = 0
                size = item.get('size')
                quoteType = item.get('quoteType')
                middle_order_pause = item.get('delay_seconds', 0)  
                buy_market_order_resp = self.place_market_order(market_place, symbol, size, "BUY", False, quoteType)
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
                    total_item_size, _, _ = self.qty_extracter(market_place, buy_order_data, symbol)
                    total_size += total_item_size
                except Exception as ex:
                    self.handle_messagee("Проблемы при попытке извлечь данные о покупке:")
                    self.handle_exception(f"{ex} на строке {inspect.currentframe().f_lineno} в файле {current_file}")
            
            for item in self.sales_share_ratio:
                try:
                    sell_order_data, sell_status = None, 0
                    share_percent, delay_seconds = Decimal(item.get("share_percent")), item.get("delay_seconds")
                    size = self.adjust_quantity(total_size, share_percent)                    
                    place_market_order_resp = self.place_market_order(market_place, symbol, size, 'SELL', False, 'q')               
                    sell_order_data, sell_status = self.process_order_response(place_market_order_resp)
                    if not sell_order_data or sell_status != 200:
                        self.handle_messagee("Проблемы при попытке создать ордер на продажу") 
                        continue                   
                    place_market_order_resp_list.append((sell_order_data, sell_status, "SELL"))
                    time.sleep(delay_seconds)
                except Exception as ex:
                    self.handle_messagee("Проблемы при попытке создать ордер на продажу:")
                    self.handle_exception(f"{ex} на строке {inspect.currentframe().f_lineno} в файле {current_file}")

        self.result_logger(place_market_order_resp_list, market_place, symbol)
        
        return True

    def trading_monitoring(self):
        first_iter = True
        parse_data = {}

        if not isinstance(self.market_place_number, int):
            print("Номер биржи выбран неверно")
            return False

        market_place = self.market_place_list[self.market_place_number - 1]

        if self.is_bible_quotes_introdaction:
            self.greeting_template()

        while True:
            try:
                time_diff_seconds = self.work_sleep_manager()
                
                # Пауза на основе планировщика
                if time_diff_seconds:
                    self.handle_messagee("Время спать!")
                    time.sleep(time_diff_seconds)
                    continue  # Пропустить остальную часть цикла, пока спим

                if first_iter:
                    first_iter = False
                    self.handle_messagee("Время поработать!")

                # Получаем данные парсера
                parse_data = self.bitget_parser()
                if not parse_data:
                    print("Парсер вернул пустые данные.")
                    time.sleep(1800)  # Ждать 30 минут, если данных нет
                    continue

                symbol = parse_data.get('symbol')
                listing_time_ms = parse_data.get('listing_time_ms')
                time_remaining = self.left_time_in_minutes_func(listing_time_ms)

                # Логирование данных
                print(f'Найдена монета: {symbol}')
                print(f'Время листинга: {self.milliseconds_to_datetime(listing_time_ms, self.tz_location)}')
                print(f'Источник: {parse_data.get("source")}')
                print(f'Оставшееся время до листинга: {time_remaining} минут')

                # Проверка оставшегося времени
                if 0 < time_remaining <= 35:
                    if not self.trading_logic_template(market_place, symbol, listing_time_ms):
                        return False
                else:
                    time.sleep(1800)  # Ждать 30 минут, если листинг слишком далек
                    continue

            except Exception as ex:
                print(f"main.py, 121 line: {ex}")
            
            # Задержка в конце каждой итерации
            time.sleep(60)
        
def main(is_display=True):
    main_logic_instanse = MAIN_LOGIC()    
    print("Инструкция находится в файле README.md. Настройки -- файл settings.json")
    if is_display:
        print("Текущие настройки: ")
        main_logic_instanse.display_params()
    print()
    intro_answer = input('Начинаем? (y/n)').strip()
    print()
    if intro_answer == "y":     
        if not main_logic_instanse.trading_monitoring():
            print("Ошибка в работе бота.")
    input('Завершить работу? (Enter)')
    print("Работа программы завершена")
    time.sleep(1)
    sys.exit()    

if __name__ == "__main__":
    main()

# python3 -m venv .venv
# source .venv/bin/activate

# pip install virtualenv
# virtualenv myenv
# myenv\Scripts\activate.bat

# pip install -r requirements.txt
# pyinstaller --onefile main.py
# python main.py

