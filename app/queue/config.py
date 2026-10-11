import os

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
STREAM_NAME = "geospatial:jobs"
CONSUMER_GROUP = "geospatial_workers"
CONSUMER_NAME_PREFIX = "worker"
DEFAULT_CLAIM_MIN_IDLE_MS = 60000  
