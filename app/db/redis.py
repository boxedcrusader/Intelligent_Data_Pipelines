import redis

# Use redis-py to create a connection
redis_client = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)

def get_redis():
    return redis_client
