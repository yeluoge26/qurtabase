"""
Cache Manager

Simple in-memory cache with TTL support.
Can be upgraded to Redis for production multi-instance deployment.
"""

import time
import json


class CacheManager:
    def __init__(self):
        self._store: dict[str, tuple[float, any]] = {}
        self._redis = None

    async def init_redis(self, redis_url: str):
        """Initialize Redis connection (optional, for production)."""
        try:
            import redis.asyncio as aioredis
            self._redis = aioredis.from_url(redis_url, decode_responses=True)
            await self._redis.ping()
        except Exception:
            self._redis = None

    async def get(self, key: str) -> any:
        """Get a cached value."""
        if self._redis:
            try:
                val = await self._redis.get(key)
                return json.loads(val) if val else None
            except Exception:
                pass

        # In-memory fallback
        if key in self._store:
            expiry, value = self._store[key]
            if time.time() < expiry:
                return value
            del self._store[key]
        return None

    async def set(self, key: str, value: any, ttl: int = 30):
        """Set a cached value with TTL in seconds."""
        if self._redis:
            try:
                await self._redis.setex(key, ttl, json.dumps(value))
                return
            except Exception:
                pass

        # In-memory fallback
        self._store[key] = (time.time() + ttl, value)

    async def delete(self, key: str):
        """Delete a cached value."""
        if self._redis:
            try:
                await self._redis.delete(key)
                return
            except Exception:
                pass

        self._store.pop(key, None)

    def cleanup(self):
        """Remove expired entries from in-memory cache."""
        now = time.time()
        expired = [k for k, (exp, _) in self._store.items() if now >= exp]
        for k in expired:
            del self._store[k]
