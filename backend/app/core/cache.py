"""
ARTHA Cache & Rate Limiting
=============================
Redis-based response caching and rate limiting.

- Response cache: keyed on hash(query + domain_filters), 1-hour TTL
- BM25 retrieval cache: separate from LLM response cache for partial hits
- Rate limiting: 20 requests/minute for free tier, configurable per plan
"""

import json
import hashlib
import logging
import time
from typing import Optional, List

from app.config import settings

logger = logging.getLogger(__name__)

# Redis client (lazy initialized)
_redis_client = None


async def get_redis():
    """Get or create the Redis client."""
    global _redis_client
    if _redis_client is None:
        try:
            import redis.asyncio as aioredis
            _redis_client = aioredis.from_url(
                settings.REDIS_URL,
                encoding="utf-8",
                decode_responses=True,
            )
            # Test connection
            await _redis_client.ping()
            logger.info(f"Redis connected: {settings.REDIS_URL}")
        except Exception as e:
            logger.warning(f"Redis connection failed (caching disabled): {e}")
            _redis_client = None
    return _redis_client


async def check_redis_health() -> bool:
    """Check Redis connectivity."""
    try:
        client = await get_redis()
        if client:
            await client.ping()
            return True
    except Exception as e:
        logger.error(f"Redis health check failed: {e}")
    return False


# ---------------------------------------------------------------------------
# Response caching
# ---------------------------------------------------------------------------
def _cache_key(query: str, domain_filters: Optional[List[str]] = None) -> str:
    """Generate a deterministic cache key from query + filters."""
    key_data = {
        "q": query.lower().strip(),
        "d": sorted(domain_filters or []),
    }
    key_hash = hashlib.sha256(json.dumps(key_data).encode()).hexdigest()[:16]
    return f"artha:response:{key_hash}"


def _retrieval_cache_key(query: str, domain_filters: Optional[List[str]] = None) -> str:
    """Cache key for BM25 retrieval results (separate from LLM response)."""
    key_data = {
        "q": query.lower().strip(),
        "d": sorted(domain_filters or []),
    }
    key_hash = hashlib.sha256(json.dumps(key_data).encode()).hexdigest()[:16]
    return f"artha:retrieval:{key_hash}"


async def get_cached_response(
    query: str,
    domain_filters: Optional[List[str]] = None,
) -> Optional[dict]:
    """Get a cached LLM response if available."""
    client = await get_redis()
    if not client:
        return None

    try:
        key = _cache_key(query, domain_filters)
        data = await client.get(key)
        if data:
            logger.info(f"Cache hit for query: '{query[:50]}...'")
            return json.loads(data)
    except Exception as e:
        logger.warning(f"Cache read error: {e}")

    return None


async def set_cached_response(
    query: str,
    response_data: dict,
    domain_filters: Optional[List[str]] = None,
    ttl: Optional[int] = None,
) -> None:
    """Cache an LLM response."""
    client = await get_redis()
    if not client:
        return

    try:
        key = _cache_key(query, domain_filters)
        await client.set(
            key,
            json.dumps(response_data),
            ex=ttl or settings.CACHE_TTL_SECONDS,
        )
        logger.info(f"Cached response for query: '{query[:50]}...'")
    except Exception as e:
        logger.warning(f"Cache write error: {e}")


async def get_cached_retrieval(
    query: str,
    domain_filters: Optional[List[str]] = None,
) -> Optional[list]:
    """Get cached BM25 retrieval results."""
    client = await get_redis()
    if not client:
        return None

    try:
        key = _retrieval_cache_key(query, domain_filters)
        data = await client.get(key)
        if data:
            return json.loads(data)
    except Exception as e:
        logger.warning(f"Retrieval cache read error: {e}")

    return None


async def set_cached_retrieval(
    query: str,
    retrieval_data: list,
    domain_filters: Optional[List[str]] = None,
) -> None:
    """Cache BM25 retrieval results (shorter TTL than response cache)."""
    client = await get_redis()
    if not client:
        return

    try:
        key = _retrieval_cache_key(query, domain_filters)
        await client.set(
            key,
            json.dumps(retrieval_data),
            ex=settings.CACHE_TTL_SECONDS // 2,  # 30 minute TTL
        )
    except Exception as e:
        logger.warning(f"Retrieval cache write error: {e}")


# ---------------------------------------------------------------------------
# Rate Limiting
# ---------------------------------------------------------------------------
RATE_LIMIT_PLANS = {
    "free": settings.RATE_LIMIT_PER_MINUTE,       # Configurable in .env
    "starter": 60,    # 60 requests per minute
    "pro": 200,       # 200 requests per minute
    "unlimited": 999999,
}


async def check_rate_limit(user_id: str, plan: str = "free") -> tuple[bool, int]:
    """
    Check and enforce rate limit for a user.

    Returns:
        Tuple of (is_allowed, remaining_requests)
    """
    client = await get_redis()
    if not client:
        # If Redis is down, allow all requests (fail-open)
        return True, -1

    limit = RATE_LIMIT_PLANS.get(plan, 20)
    key = f"artha:ratelimit:{user_id}"

    try:
        # Use a sliding window counter
        current_time = int(time.time())
        window_start = current_time - 60  # 1-minute window

        pipe = client.pipeline()
        # Remove old entries
        pipe.zremrangebyscore(key, 0, window_start)
        # Count current window
        pipe.zcard(key)
        # Add current request
        pipe.zadd(key, {str(current_time): current_time})
        # Set expiry on the key
        pipe.expire(key, 120)

        results = await pipe.execute()
        current_count = results[1]  # zcard result

        if current_count >= limit:
            logger.warning(f"Rate limit exceeded for user {user_id} (plan: {plan})")
            return False, 0

        remaining = limit - current_count - 1
        return True, remaining

    except Exception as e:
        logger.warning(f"Rate limit check error (allowing): {e}")
        return True, -1


# ---------------------------------------------------------------------------
# Cleanup
# ---------------------------------------------------------------------------
async def close_redis() -> None:
    """Close the Redis connection."""
    global _redis_client
    if _redis_client:
        await _redis_client.close()
        _redis_client = None
        logger.info("Redis connection closed")
