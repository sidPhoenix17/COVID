import threading
from lib.redis import redis
import time
from database_entry import send_sms
import json

class BaseConsumer(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)


    def run(self):
        while True:
            try:
                if redis.llen(self.redis_key) > 0:
                    redis_message = redis.lpop(self.redis_key).decode("utf-8") 
                    self.process_message(redis_message)
                else:
                    time.sleep(1)
            except Exception as e:
                print("Error in running base consumer ", str(e))
    
