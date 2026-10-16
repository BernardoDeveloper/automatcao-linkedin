from datetime import date, datetime, timedelta

from linkedin_ia import state

NOW = datetime(2026, 10, 16, 19, 0).astimezone()


def test_first_run_uses_the_default_days(make_config):
    cfg = make_config()
    assert state.window_start(cfg, NOW) == NOW - timedelta(days=14)


def test_later_runs_start_at_the_last_successful_run(make_config):
    cfg = make_config()
    previous = NOW - timedelta(days=3)
    state.record_run(cfg, previous)
    assert state.window_start(cfg, NOW) == previous


def test_desde_overrides_the_recorded_run(make_config):
    cfg = make_config()
    state.record_run(cfg, NOW - timedelta(days=3))
    start = state.window_start(cfg, NOW, date(2026, 9, 1))
    assert (start.year, start.month, start.day, start.hour) == (2026, 9, 1, 0)


def test_a_corrupt_state_file_counts_as_no_run(make_config):
    cfg = make_config()
    cfg.state_file.parent.mkdir(parents=True)
    cfg.state_file.write_text("lixo")
    assert state.window_start(cfg, NOW) == NOW - timedelta(days=14)
