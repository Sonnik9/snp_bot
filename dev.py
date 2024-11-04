    
    # def milliseconds_to_datetime_for_parser(self, milliseconds):        
    #     seconds, milliseconds = divmod(milliseconds, 1000)
    #     time = datetime.datetime.utcfromtimestamp(seconds)        
    #     return time.strftime('%Y-%m-%d %H:%M:%S')

    # def work_sleep_manager(self):
    #     if not self.work_to or not self.sleep_to:
    #         return None
    #     current_time_utc = time.gmtime(time.time())
    #     current_hour = current_time_utc.tm_hour
    #     if not (self.sleep_to <= current_hour < self.work_to):
    #         current_time_utc = time.gmtime(time.time())
    #         desired_time_utc = time.struct_time((current_time_utc.tm_year, current_time_utc.tm_mon, current_time_utc.tm_mday + 1, self.sleep_to, 0, 0, 0, 0, 0))
    #         time_diff_seconds = time.mktime(desired_time_utc) - time.mktime(current_time_utc)
    #         print("It is time to rest! Let's go to bed!")
    #         return time_diff_seconds
    #     return None

# from datetime import datetime, timezone
# import time

# # current_utc_time_ms = int(datetime.now(timezone.utc).timestamp() * 1000)
# print(int(datetime.now(timezone.utc).timestamp() * 1000))
# print(int(time.time()* 1000))
