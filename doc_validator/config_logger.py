import logging
from pathlib import Path

log_dir = Path('output/logs')
log_dir.mkdir(parents=True, exist_ok=True)

log_file = log_dir / 'log.log'

logging.basicConfig(level=logging.WARNING,
                    filename=str(log_file),
                    filemode="w",
                    format='[%(asctime)s] - %(levelname)s - %(message)s',
                    datefmt='%d-%b-%y %H:%M:%S',
                    encoding="utf-8")

logger = logging.getLogger(__name__)
