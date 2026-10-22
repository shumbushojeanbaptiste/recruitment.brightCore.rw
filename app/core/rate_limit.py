
import logging
from collections.abc import Callable

from fastapi import HTTPException, Request, status

logger = logging.getLogger(__name__)

# INCR and EXPIRE happen in one atomic Redis operation.
# The key expires automatically after the configured time window.
_RATE_LIMIT_SCRIPT = """
local count = redis.call('INCR', KEYS[1])
if count == 1 then
    redis.call('EXPIRE', KEYS[1], ARGV[1])
end
local ttl = redis.call('TTL', KEYS[1])
return {count, ttl}
"""


def rate_limit(
    *,
    limit: int,
    window_seconds: int,
    key_prefix: str,
) -> Callable:
    if limit < 1 or window_seconds < 1:
        raise ValueError("Rate limit and window must be positive")

    async def dependency(request: Request) -> None:
        # Use the direct connection address. Only use forwarded client
        # IP headers when the application is behind a trusted proxy
        # configured to overwrite those headers.
        client_ip = (
            request.client.host
            if request.client is not None
            else "unknown"
        )

        redis_client = getattr(request.app.state, "redis", None)

        if redis_client is None:
            logger.error("Redis client is unavailable for rate limiting")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Request protection is temporarily unavailable",
            )

        key = f"brightcore:rate:{key_prefix}:{client_ip}"

        try:
            result = await redis_client.eval(
                _RATE_LIMIT_SCRIPT,
                1,
                key,
                window_seconds,
            )
            count = int(result[0])
            retry_after = max(int(result[1]), 1)
        except Exception as exc:
            # Fail closed: these protected operations are not allowed
            # when the rate limiter cannot verify the request count.
            logger.error(
                "Redis rate limiter failed for key prefix %s: %s",
                key_prefix,
                type(exc).__name__,
            )
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Request protection is temporarily unavailable",
            ) from exc

        if count > limit:
            logger.warning(
                "Rate limit exceeded for key prefix %s",
                key_prefix,
            )
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Too many requests. Please try again later.",
                headers={"Retry-After": str(retry_after)},
            )

    return dependency
