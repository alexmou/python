
# ───────────────────────────────────────────────
# Module: log_config.py
# ───────────────────────────────────────────────

import logging

logging.basicConfig(
    format='[%(levelname)s] %(asctime)s - %(message)s',
    level=logging.CRITICAL
)

logger = logging.getLogger(__name__)
