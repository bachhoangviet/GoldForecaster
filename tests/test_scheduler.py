"""Scheduler configuration tests."""

from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger


def test_scheduler_jobs_prevent_overlap():
    scheduler = BlockingScheduler()

    scheduler.add_job(
        lambda: None,
        CronTrigger(hour="0,6,12,18", minute=0),
        id="news-ingestion",
        max_instances=1,
        coalesce=True,
    )
    scheduler.add_job(
        lambda: None,
        CronTrigger(minute=0),
        id="macro-ingestion",
        max_instances=1,
        coalesce=True,
    )

    news_job = scheduler.get_job("news-ingestion")
    macro_job = scheduler.get_job("macro-ingestion")

    assert news_job is not None
    assert macro_job is not None
    assert news_job.max_instances == 1
    assert macro_job.max_instances == 1
    assert news_job.coalesce is True
    assert macro_job.coalesce is True
