from linkedin_ia import notify


def test_sends_the_text_under_the_linkedin_title(monkeypatch):
    calls = []
    monkeypatch.setattr(notify.shutil, "which", lambda name: f"/usr/bin/{name}")
    monkeypatch.setattr(notify.subprocess, "run", lambda args, **kw: calls.append(args))
    notify.desktop("1 post para revisar")
    assert calls == [
        ["/usr/bin/notify-send", "--app-name=linkedin", "--", "LinkedIn", "1 post para revisar"]
    ]


def test_is_silent_without_notify_send(monkeypatch):
    monkeypatch.setattr(notify.shutil, "which", lambda name: None)
    monkeypatch.setattr(
        notify.subprocess, "run", lambda *a, **kw: (_ for _ in ()).throw(AssertionError)
    )
    notify.desktop("nada")


def test_markup_in_the_text_is_shown_as_text(monkeypatch):
    calls = []
    monkeypatch.setattr(notify.shutil, "which", lambda name: f"/usr/bin/{name}")
    monkeypatch.setattr(notify.subprocess, "run", lambda args, **kw: calls.append(args))
    notify.desktop('<a href="x">Título</a> & cia')
    assert calls[0][-1] == '&lt;a href="x"&gt;Título&lt;/a&gt; &amp; cia'
