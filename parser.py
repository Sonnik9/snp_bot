import requests
from bs4 import BeautifulSoup
from joblib import Parallel, delayed
import time
from random import choice
from utils import ProcessUtils

parse_url_api = "https://api.bitget.com/api/v2/public/annoucements?&annType=coin_listings&language=en_US"

user_agents = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.182 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.182 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.87 Safari/537.36",
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/84.0.4147.89 Safari/537.36',
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
]

bitget_headers = {
    'authority': 'www.bitget.com',    
    # 'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
    'accept-language': 'en-US,en;q=0.9',
    'cache-control': 'max-age=0',
    'referer': 'https://www.bitget.com/',
    'sec-fetch-dest': 'document',
    'sec-fetch-mode': 'navigate',
    'sec-fetch-site': 'none',
    'sec-fetch-user': '?1',
    'upgrade-insecure-requests': '1',
    'User-Agent': choice(user_agents)
}

class BitgetParser(ProcessUtils):
    def __init__(self) -> None:
        super().__init__()
        self.bitget_parser_session = requests.Session()
        if self.is_proxy:
            self.bitget_parser_session.proxies.update(self.proxiess)

    def links_multiprocessor(self, data, cur_time, cpu_count=2): 
        total_list = []
        try:
            res = Parallel(n_jobs=cpu_count, prefer="threads")(delayed(lambda item: self.bitget_links_handler(item, cur_time))(item) for item in data)
            for x in res: 
                if x:               
                    try:                    
                        total_list.append(x)
                    except:
                        pass 
        except:
            pass
        return total_list

    def bitget_links_handler(self, data_item, cur_time):
        try:
            bitget_headers['User-Agent'] = choice(user_agents)
            link = data_item['annUrl']
            r = self.bitget_parser_session.get(url=link, headers=bitget_headers, proxies=self.proxiess if self.is_proxy else None)

            if r is None or r.status_code != 200:
                print(r)
                return {}
            soup = BeautifulSoup(r.text, 'html.parser')
            listing_time_all_potential_string = soup.find('div', class_='ArticleDetails_actice_details_main__oIjfu').get_text()
            trading_time_str = [x for x in listing_time_all_potential_string.split('\n') if "Trading Available:" in x][0].replace("Trading Available:", "").strip()
            listing_time = self.from_string_to_date_time(trading_time_str)

            if listing_time > cur_time:
                symbol_data = self.symbol_extracter(data_item['annTitle'])
                if symbol_data:
                    symbol = None
                    symbol = [x.strip() + 'USDT' for x in symbol_data if x.strip()][0]
                    return {                                
                                "symbol": symbol,                                
                                "listing_time_ms": listing_time,
                                "source": link       
                           }
               
        except Exception as ex:
            pass
                   
        return {}
                 
    def bitget_parser(self):
        try:
            start_time = self.get_start_of_day()                    
            r = requests.get(parse_url_api)
            if r is not None and r.status_code == 200:
                r_j = r.json()
                data = r_j["data"]        
                data = [{**x, "cTime": int(float(x["cTime"]))} for x in data if int(float(x["cTime"])) > start_time]
                # print(data)
                cur_time = int(time.time()* 1000)
                bitget_headers['User-Agent'] = choice(user_agents)
                pars_data = self.links_multiprocessor(data, cur_time)
                set_list = sorted(pars_data, key=lambda x: x["listing_time_ms"], reverse=False)
                return set_list[0]
        except Exception as ex:
            pass
        return {}
    
# print(BitgetParser().bitget_parser())
