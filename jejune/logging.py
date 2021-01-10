import logging
import os


level = logging.INFO
if 'JEJUNE_DEBUG' in os.environ:
    level = logging.DEBUG


logging.basicConfig(
    level=level,
    format="[%(asctime)s] %(levelname)s: %(message)s",
    handlers=[logging.StreamHandler()]
)
