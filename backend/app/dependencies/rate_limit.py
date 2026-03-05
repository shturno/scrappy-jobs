"""Rate limiting dependency — 5 requests per minute per IP."""

from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
