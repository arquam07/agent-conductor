"""Worker: pulls jobs off the queue and runs the agent.
This is the consumer half of Diagram 1. Graceful shutdown ensures an in-flight
job finishes before the process exits (K8s sends SIGTERM before killing a pod)."""
import argparse
import json
import logging
import signal

from app.agent.graph import run_agent
from app.shared import queue
from app.shared.db import get_session, init_db
from app.shared.logging_setup import log_block, setup_logging
from app.shared.models import Job, JobStatus

logger = logging.getLogger("worker")

_shutdown = False  # flipped by SIGTERM/SIGINT; loop exits after current job


def _handle_signal(signum, _frame):
    global _shutdown
    logger.info("received signal %s, finishing current job then exiting", signum)
    _shutdown = True


def _process_one(job_id: str) -> None:
    # Block: load job + mark running
    with get_session() as session:
        job = session.get(Job, job_id)
        if job is None:
            logger.warning("job %s not found, skipping", job_id)
            return
        job.status = JobStatus.running
        task, params = job.task, json.loads(job.params or "{}")
    log_block(logger, "mark running", f"job_id={job_id}")

    # Block: execute agent (see Diagram 2)
    try:
        result = run_agent(task, params)
        status, result_val, error_val = JobStatus.done, result, None
    except Exception as e:
        logger.exception("job %s failed", job_id)
        status, result_val, error_val = JobStatus.failed, None, str(e)

    # Block: persist outcome
    with get_session() as session:
        job = session.get(Job, job_id)
        if job is not None:
            job.status = status
            job.result = result_val
            job.error = error_val
    log_block(logger, "persist", f"job_id={job_id} status={status.value}")


def run_loop() -> None:
    signal.signal(signal.SIGTERM, _handle_signal)
    signal.signal(signal.SIGINT, _handle_signal)
    init_db()
    logger.info("worker started, polling queue")

    while not _shutdown:
        # Block: pull job_id (blocking pop, returns None on timeout)
        job_id = queue.dequeue()
        if job_id is None:
            continue  # timeout, re-check shutdown flag and poll again
        log_block(logger, "pull", f"job_id={job_id}")
        _process_one(job_id)

    logger.info("worker shut down cleanly")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--debug", action="store_true", help="enable debug logging")
    args = parser.parse_args()
    setup_logging(debug=args.debug, component="worker")
    run_loop()


if __name__ == "__main__":
    main()