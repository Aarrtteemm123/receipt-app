import json

from config import redis_client


class RedisSvc:
    def hset(self, name, key, value):
        data = json.dumps(value)
        redis_client.hset(name, mapping={key: data})

    def hget(self, name, key):
        data = redis_client.hget(name, key)
        if not data:
            return
        return json.loads(data)

    def delete(self, key):
        redis_client.delete(key)
