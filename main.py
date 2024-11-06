import asyncio
import datetime
from enum import Enum
import random
import time
import uuid
from fastapi import FastAPI, BackgroundTasks
from pydantic import BaseModel
import requests

jobs_store = {
}

class Status(str, Enum):
    PENDING = "pending"
    ERROR = "error"
    COMPLETED = "completed"

class StatusResponse(BaseModel):
    status: Status

class TranslationJob:
    def __init__(self, duration: float, webhook_url: str, error_probability: float = 0.1):
        self.id = uuid.uuid4()
        self.start_time = time.time()
        self.duration = duration
        self.webhook_url = webhook_url
        self.error_probability = error_probability
        self.has_error = random.random() < error_probability
        
    def get_status(self) -> Status:
        if self.has_error:
            return Status.ERROR
        if time.time() - self.start_time > self.duration:
            return Status.COMPLETED
        return Status.PENDING

    def to_dict(self):
        return {
            "id": str(self.id),
            "created_at": self.start_time,
            "duration": self.duration,
            "status": self.get_status()
        }

class WebhookService:
    MAX_RETRIES = 3
    RETRY_DELAY = 5  # seconds

    @staticmethod
    async def send_webhook(job: TranslationJob) -> bool:
        if not job.webhook_url:
            return True

        payload = {
            "job_id": str(job.id),
            "status": job.get_status(),
            "created_at": job.start_time,
            "event_type": "translation.status_update"
        }

        for attempt in range(WebhookService.MAX_RETRIES):
            try:
                response = requests.post(
                    job.webhook_url,
                    json=payload,
                    timeout=5,
                    headers={"Content-Type": "application/json"}
                )
                if response.ok:
                    job.last_webhook_attempt = datetime.datetime.now(datetime.timezone.utc)
                    print("sent webhook")
                    return True
                
            except requests.RequestException as e:
                print("ERROR")                
            job.webhook_attempts += 1
            await asyncio.sleep(WebhookService.RETRY_DELAY * (2 ** attempt))

        return False



app = FastAPI()

from pydantic import BaseModel

class TranslationRequest(BaseModel):
    duration: float
    webhook_url: str

@app.post("/translations/status/")
async def create_translation(request: TranslationRequest, background_tasks: BackgroundTasks):
    job = TranslationJob(
        duration=request.duration,
        webhook_url=request.webhook_url
    )
    jobs_store[job.id] = job
    background_tasks.add_task(_monitor_job_status, job)
    return job.to_dict()

@app.get("/translations/status/{id}")
async def get_status(id: str):   
    if id not in jobs_store:
        return {"status": Status.ERROR}
    return {
        "id": id,
        "duration": jobs_store[id].duration,
        "status": jobs_store[id].get_status(),
    }

@app.get("/translation/status")
async def get_all_jobs():
    jobs = [job.to_dict() for job in jobs_store.values()]
    return {"jobs": jobs}

async def _monitor_job_status(job: TranslationJob):
    print("STARTED RUNNING IN THE BACKGROUND")
    print('\n' * 5)
    
    previous_status = job.get_status()
    while True:
        current_status = job.get_status()
        
        if current_status != previous_status:
            await WebhookService.send_webhook(job)
            
            if current_status in [Status.COMPLETED, Status.ERROR]:
                break
                
        previous_status = current_status
        await asyncio.sleep(1)
