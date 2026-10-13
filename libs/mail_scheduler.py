"""In-process APScheduler jobs from ``templates/reports/*.toml``."""

from __future__ import annotations

import logging
import threading

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from libs.config import get_alerts_config
from libs.mail_reports import run_report
from libs.mail_state import MailState
from libs.report_definitions import load_report_definitions

_LOG = logging.getLogger(__name__)

_scheduler: BackgroundScheduler | None = None
_lock = threading.Lock()


def _job_for_report(report_id: str) -> None:
    try:
        cfg = get_alerts_config()
    except Exception as exc:
        _LOG.warning("Report %s skipped (config): %s", report_id, exc)
        return
    if not cfg.get("enabled"):
        return
    state = MailState.load(cfg["sqlite_path"])
    try:
        run_report(report_id, cfg, state)
    except Exception:
        _LOG.exception("Scheduled report %s failed", report_id)


def start_mail_scheduler() -> None:
    global _scheduler
    with _lock:
        if _scheduler is not None:
            return
        try:
            cfg = get_alerts_config()
        except Exception as exc:
            _LOG.info("Mail scheduler not started: %s", exc)
            return
        if not cfg.get("enabled"):
            _LOG.info("Mail scheduler not started ([alerts] enabled = false)")
            return

        reports = [r for r in load_report_definitions() if r.enabled]
        if not reports:
            _LOG.warning("Mail scheduler not started: no templates/reports/*.toml")
            return

        scheduler = BackgroundScheduler(timezone="UTC")
        for report in reports:
            trigger_kwargs: dict = {
                "hour": report.schedule_hour,
                "minute": report.schedule_minute,
            }
            if report.schedule_day_of_week:
                trigger_kwargs["day_of_week"] = report.schedule_day_of_week
            scheduler.add_job(
                _job_for_report,
                CronTrigger(**trigger_kwargs),
                args=[report.id],
                id=f"mail_report_{report.id}",
                replace_existing=True,
            )
        scheduler.start()
        _scheduler = scheduler
        _LOG.info(
            "Mail scheduler started for %s report(s): %s",
            len(reports),
            ", ".join(r.id for r in reports),
        )
