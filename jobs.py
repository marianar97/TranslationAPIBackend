import random
import time
import uuid
from models import Status

class TranslationJob:
    def __init__(self, duration: float, webhook_url: str, error_probability: float = 0.1):
        self.id = uuid.uuid4()
        self.start_time = time.time()
        self.duration = duration
        self.error_probability = error_probability
        self.has_error = random.random() < error_probability
        self.webhook_url = webhook_url

    def get_status(self) -> Status:
        if self.has_error:
            return Status.ERROR
        if time.time() - self.start_time > self.duration:
            return Status.COMPLETED
        return Status.PENDING

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "webhook_url": self.webhook_url,
            "created_at": self.start_time,
            "duration": self.duration,
            "status": self.get_status(),
        }