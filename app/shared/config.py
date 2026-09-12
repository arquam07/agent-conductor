"""Central config, loaded from environment. Nothing hardcoded per-env."""
import os


class Settings:
    # Redis (queue)
    redis_url: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    queue_key: str = os.getenv("QUEUE_KEY", "agentflow:jobs")

    # Postgres (results store)
    database_url: str = os.getenv(
        "DATABASE_URL", "postgresql+psycopg://postgres:postgres@localhost:5432/agentflow"
    )

    # Agent
    max_steps: int = int(os.getenv("AGENT_MAX_STEPS", "8"))
    llm_model: str = os.getenv("LLM_MODEL", "claude-sonnet-4-5")

    # Worker
    poll_timeout: int = int(os.getenv("WORKER_POLL_TIMEOUT", "5"))  # seconds

    # Job retention (cleanup cronjob)
    retention_hours: int = int(os.getenv("RETENTION_HOURS", "24"))


settings = Settings()