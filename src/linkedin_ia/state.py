"""The collection window, and the last successful run that starts it."""

from datetime import date, datetime, timedelta

from linkedin_ia.config import Config


def last_run(config: Config) -> datetime | None:
    try:
        return datetime.fromisoformat(config.state_file.read_text(encoding="utf-8").strip())
    except (FileNotFoundError, ValueError):
        return None


def record_run(config: Config, started: datetime) -> None:
    config.state_file.parent.mkdir(parents=True, exist_ok=True)
    config.state_file.write_text(started.isoformat() + "\n", encoding="utf-8")


def window_start(config: Config, now: datetime, since: date | None = None) -> datetime:
    if since is not None:
        return datetime.combine(since, datetime.min.time()).astimezone()
    previous = last_run(config)
    if previous is not None:
        return previous
    return now - timedelta(days=config.default_days)
