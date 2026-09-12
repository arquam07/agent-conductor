"""Queue client. Redis list used as a FIFO job queue.
This is the seam that decouples API (producer) from workers (consumers)."""
import redis

from app.shared.config import settings

_client = redis.from_url(settings.redis_url, decode_responses=True)


def enqueue(job_id: str) -> None:
    """Push a job_id onto the queue. Called by the API."""
    _client.lpush(settings.queue_key, job_id)


def dequeue(timeout: int | None = None) -> str | None:
    """Blocking pop of one job_id. Called by workers. Returns None on timeout.
    Blocking pop lets idle workers wait without busy-looping."""
    t = settings.poll_timeout if timeout is None else timeout
    item = _client.brpop(settings.queue_key, timeout=t)
    return item[1] if item else None


def queue_depth() -> int:
    """Pending job count. KEDA scales workers on this."""
    return _client.llen(settings.queue_key)


def ping() -> bool:
    return bool(_client.ping())