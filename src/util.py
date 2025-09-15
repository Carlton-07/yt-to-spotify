import os
import time
import logging
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="[%(levelname)s] %(asctime)s %(name)s: %(message)s",
)

log = logging.getLogger("yt2sp")


def env_bool(key: str, default: bool = False) -> bool:
    val = os.getenv(key, str(default)).lower().strip()
    return val in {"1", "true", "yes", "y"}


def sleep_with_jitter(base: float = 1.0, jitter: float = 0.25):
    import random
    time.sleep(max(0, base + random.uniform(-jitter, jitter)))
