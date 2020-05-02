from consumers.sms_sender import SMSSender
import threading

class ConsumerFactory():
    def get_consumer(self, name):
        return self.consumer_mapping()[name]

    def consumer_mapping(self):
        return {
            "sms_messages": SMSSender()
        }

    def get_all(self):
        return self.consumer_mapping().keys()

if __name__ == "__main__":
    consumerFactory = ConsumerFactory()
    consumers = consumerFactory.get_all()
    for consumer in consumers:
        executor = consumerFactory.get_consumer(consumer)
        executor.start()