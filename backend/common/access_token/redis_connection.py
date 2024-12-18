import redis

class RedisConnection:
    def __init__(self, host='localhost', port=6379, db=0):
        self.redis_client = redis.StrictRedis(host=host, port=port, db=db, decode_responses=True)

    def hset(self, key, field, value):
        """Set a field in a hash."""
        self.redis_client.hset(key, field, value)

    def hget(self, key, field):
        """Get a field from a hash."""
        return self.redis_client.hget(key, field)

    def hgetall(self, key):
        """Get all fields in a hash."""
        return self.redis_client.hgetall(key)

    def delete(self, key):
        """Delete a key from Redis."""
        self.redis_client.delete(key)
