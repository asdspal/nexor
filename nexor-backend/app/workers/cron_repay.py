"""Auto-repayment cron worker (Blueprint Section 3.1 / 7.4 / 9).

Responsibilities:
- Daily job invokes internal POST /api/repayment/trigger to process repayments.
- Uses APScheduler BackgroundScheduler.
"""

from __future__ import annotations

import logging
import os

import httpx
from apscheduler.schedulers.background import BackgroundScheduler

from app.core.config import CRON_INTERNAL_KEY, REPAY_CRON_ENABLED, REPAY_CRON_URL

logger = logging.getLogger(__name__)


def _trigger_repay() -> None:
    try:
        resp = httpx.post(REPAY_CRON_URL, headers={"X-Cron-Key": CRON_INTERNAL_KEY}, timeout=30.0)
        resp.raise_for_status()
        logger.info("repay trigger success", extra={"status": resp.status_code, "body": resp.json()})
    except Exception as exc:  # noqa: BLE001
        logger.error("repay trigger failed", exc_info=exc)


def start_scheduler() -> BackgroundScheduler | None:
    if not REPAY_CRON_ENABLED:
        logger.info("repay cron disabled via config")
        return None

    scheduler = BackgroundScheduler(timezone=os.getenv("TZ", "UTC"))
    scheduler.add_job(_trigger_repay, "interval", hours=24, id="repay-trigger", replace_existing=True)
    scheduler.start()
    logger.info("repay cron scheduler started")
    return scheduler


def main() -> None:
    # For standalone execution
    start_scheduler()
    import time

    try:
        while True:
            time.sleep(60)
    except KeyboardInterrupt:
        logger.info("repay cron interrupted")


if __name__ == "__main__":
    main()
