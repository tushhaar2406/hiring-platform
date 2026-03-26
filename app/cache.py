import redis
import json
import os
from dotenv import load_dotenv

load_dotenv()

# connect to Redis
redis_client = redis.from_url(
    os.getenv("REDIS_URL"),
    decode_responses=True    # returns strings instead of bytes
)

# ─── Save data to cache ────────────────────────────────────
def set_cache(key: str, data: any, expire_seconds: int = 300):
    try:
        # convert Python object to JSON string for storage
        redis_client.setex(
            name  = key,
            time  = expire_seconds,   # auto-expires after this many seconds
            value = json.dumps(data)
        )
    except Exception as e:
        print(f"Cache set error: {e}")

# ─── Get data from cache ───────────────────────────────────
def get_cache(key: str) -> any:
    try:
        data = redis_client.get(key)
        if data:
            return json.loads(data)   # convert JSON string back to Python object
        return None
    except Exception as e:
        print(f"Cache get error: {e}")
        return None

# ─── Delete specific cache key ─────────────────────────────
def delete_cache(key: str):
    try:
        redis_client.delete(key)
    except Exception as e:
        print(f"Cache delete error: {e}")

# ─── Clear all cache keys matching a pattern ───────────────
def clear_cache_pattern(pattern: str):
    try:
        keys = redis_client.keys(pattern)
        if keys:
            redis_client.delete(*keys)
    except Exception as e:
        print(f"Cache clear error: {e}")