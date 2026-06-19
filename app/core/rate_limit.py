from app.core.settings import settings
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(
    key_func=get_remote_address,
    storage_uri=f"{settings.redis_url}{settings.redis_limiter_db}",
    default_limits=["60/minute"],
)
