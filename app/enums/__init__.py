from enum import Enum

class Status(Enum):
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"