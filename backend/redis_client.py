import os
import redis.asyncio as redis
from typing import Optional

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")

class RedisClient:
    _instance: Optional[redis.Redis] = None

    @classmethod
    def get_client(cls) -> redis.Redis:
        if cls._instance is None:
            cls._instance = redis.from_url(REDIS_URL, decode_responses=True)
        return cls._instance

    @classmethod
    async def close(cls):
        if cls._instance:
            await cls._instance.aclose()
            cls._instance = None

def get_redis_client() -> redis.Redis:
    return RedisClient.get_client()
