import logging
from typing import List
from fastapi import FastAPI
import fastapi
from pydantic import UUID4
from models import TranslationRequest, JobResponse
from jobs import TranslationJob

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler()
    ]
)

app = FastAPI()
jobs_store = {}


@app.post("/translations/status/", status_code=201)
async def create_translation(request: TranslationRequest) -> JobResponse:
    logging.info(f"Creating new translation job with duration={request.duration} and webhook_url={request.webhook_url}")
    job = TranslationJob(duration=request.duration, webhook_url=request.webhook_url)
    jobs_store[job.id] = job
    return JobResponse(**job.to_dict())

@app.get("/translations/status/{id}")
async def get_status(id: UUID4) -> JobResponse:
    if id not in jobs_store:
        logging.warning(f"Job with id {id} was not found")
        raise fastapi.HTTPException(status_code=404, detail=f"Job with id: {id} was not found")
    return JobResponse(**jobs_store[id].to_dict())


@app.get("/translations/status", response_model=dict[str, List[JobResponse]])
async def get_all_jobs():
    logging.info("Retrieving all jobs")
    jobs = [job.to_dict() for job in jobs_store.values()]
    return {"jobs": jobs}

if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app)