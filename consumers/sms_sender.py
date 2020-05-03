import threading
from lib.redis import redis
import time
from database_entry import send_sms
import json
from consumers.base_consumer import BaseConsumer
from database_entry import send_sms_to_phone

redis_key = "sms_channel"

class SMSSender(BaseConsumer):
    def __init__(self):
        super().__init__()
        self.name = "SMSSender"
        self.redis_key = redis_key
        self.sleep_time = 2

    def process_message(self, redisMessage):
        try:
            print("Processing message" + redisMessage, flush=True)
            info = json.loads(redisMessage)
            phone_number = info.get('phone_number')
            int_phone_number = int(phone_number)
            message = info.get('text')
            message_type = info.get("type", "Transactional")
            try:
                SMSSender.send(int_phone_number, message, message_type)
            except Exception as e:
                print("Problem in sending sms ", redisMessage, str(e))
        except Exception as e:
            print("Problem in parsing redisMessage " + str(e), redisMessage)



    @classmethod
    def send(cls, phone_number, message, message_type):
        send_sms_to_phone(message, int(phone_number), message_type)