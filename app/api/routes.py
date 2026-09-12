"""API routes. Blocks here match Diagram 1 (job lifecycle) labels."""
import json
import logging

from fastapi import APIRouter, HTTPException

from app.shared import queue
from app.shared.db import get_session
from app.shared.logging_setup import log_block
from app.shared.models import Job, JobDetail, JobRequest, JobResponse, JobStatus

router = APIRouter()
logger = logging.getLogger("api")


@router.post("/jobs", response_model=JobResponse, status_code=202)
def submit_job(req: JobRequest) -> JobResponse:
    # Block: validate + create record  (in: job spec -> out: job row, status=queued)
    if not req.task.strip():
        raise HTTPException(status_code=422, detail="task must not be empty")

    job = Job(task=req.task, params=json.dumps(req.params))
    with get_session() as session:
        session.add(job)
        session.flush()  # populate job.id before the session closes
        job_id = job.id
    log_block(logger, "validate+create", f"job_id={job_id} status=queued")

    # Block: enqueue job_id  (in: job_id -> out: id pushed to Redis)
    queue.enqueue(job_id)
    log_block(logger, "enqueue", f"job_id={job_id}")

    # Block: respond 202
    return JobResponse(job_id=job_id, status=JobStatus.queued)


@router.get("/jobs/{job_id}", response_model=JobDetail)
def get_job(job_id: str) -> JobDetail:
    # Block: client GET /jobs/{id}  (in: job_id -> out: status + result)
    with get_session() as session:
        job = session.get(Job, job_id)
        if job is None:
            raise HTTPException(status_code=404, detail="job not found")
        return JobDetail(
            job_id=job.id,
            status=job.status,
            task=job.task,
            result=job.result,
            error=job.error,
        )