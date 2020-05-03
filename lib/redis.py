import redis
from settings import redis_host

redis = redis.Redis(host=redis_host)    