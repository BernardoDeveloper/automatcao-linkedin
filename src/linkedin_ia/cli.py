"""The `linkedin` command: coletar, checar, fila, login, publicar."""

import argparse
import getpass
import sys
from datetime import date, datetime, timedelta
from pathlib import Path

from linkedin_ia import check, credentials, digest, drafts, linkedin_api, notify, publisher, state
from linkedin_ia import config as config_module


def coletar(args: argparse.Namespace, config: config_module.Config) -> int:
    started = datetime.now().astimezone()
    since = state.window_start(config, started, args.desde)
    path = digest.write(digest.collect(config, since, started), config)
    state.record_run(config, started)
    print(path)
    return 0


def _warn_disabled(config: config_module.Config) -> None:
    for name in check.disabled_rules(config):
        print(f"aviso: {name} vazio em config.toml — essa regra não roda", file=sys.stderr)


def checar(args: argparse.Namespace, config: config_module.Config) -> int:
    _warn_disabled(config)
    findings = [f for path in args.arquivos for f in check.check(path, config)]
    for f in findings:
        print(f"{f.path}:{f.line}: {f.rule}: {f.text}")
    if findings:
        return 2
    print(f"ok: {len(args.arquivos)} rascunho(s) sem achados")
    return 0


def fila(args: argparse.Namespace, config: config_module.Config) -> int:
    _warn_disabled(config)
    queue = drafts.queue(config)
    print(f"second brain: {config.second_brain}")
    print(f"pasta: {config.drafts_dir}")
    if not queue:
        print("nenhum rascunho")
        return 0
    blocked = False
    for status in (*drafts.STATUSES, drafts.OTHER):
        group = sorted(
            (d for d in queue if d.group == status),
            key=lambda d: str(d.meta.get("publicar_em") or "9999"),
        )
        if not group:
            continue
        print(f"\n{status} ({len(group)})")
        for draft in group:
            mark = f"  [{draft.status or 'sem status'}]" if status == drafts.OTHER else ""
            findings = check.check(draft.path, config)
            if findings:
                mark += f'  ✗ {len(findings)} achado(s) — linkedin checar "{draft.path}"'
                blocked = blocked or status == "aprovado"
            when = draft.meta.get("publicar_em") or "sem data"
            print(f"  {when}  {draft.title}{mark}")
    return 2 if blocked else 0


def login(args: argparse.Namespace, config: config_module.Config) -> int:
    secret = getpass.getpass("Token do LinkedIn (gerador do LinkedIn Developers): ").strip()
    if not secret:
        print("nenhum token informado", file=sys.stderr)
        return 1
    client = linkedin_api.Client(secret, config.api_version, args.transport)
    try:
        person, name = client.member()
    except linkedin_api.ApiError as error:
        print(f"token recusado pelo LinkedIn ({error})", file=sys.stderr)
        return 2
    except linkedin_api.NoAnswer as error:
        print(f"LinkedIn não respondeu: {error}", file=sys.stderr)
        return 1
    expires = datetime.now().astimezone() + timedelta(days=args.dias)
    credentials.save(config.token_file, credentials.Token(secret, person, name, expires))
    print(f"ok: token de {name or person} válido até {expires:%Y-%m-%d}, em {config.token_file}")
    return 0


def publicar(args: argparse.Namespace, config: config_module.Config) -> int:
    _warn_disabled(config)
    return publisher.run(
        config, datetime.now().astimezone(), notify.desktop, args.transport, not args.simular
    )


def main(
    argv: list[str] | None = None,
    config: config_module.Config | None = None,
    transport: linkedin_api.Transport = linkedin_api.urllib_transport,
) -> int:
    parser = argparse.ArgumentParser(prog="linkedin", description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)

    collect = commands.add_parser("coletar", help="write the digest of the window")
    collect.add_argument("--desde", type=date.fromisoformat, metavar="AAAA-MM-DD")
    collect.set_defaults(run=coletar)

    verify = commands.add_parser("checar", help="run the confidentiality check on drafts")
    verify.add_argument("arquivos", nargs="+", type=Path)
    verify.set_defaults(run=checar)

    listing = commands.add_parser("fila", help="list the drafts by status")
    listing.set_defaults(run=fila)

    sign_in = commands.add_parser("login", help="store a token from LinkedIn's token generator")
    sign_in.add_argument("--dias", type=int, default=60, help="token lifetime in days")
    sign_in.set_defaults(run=login)

    publish = commands.add_parser(
        "publicar", help="apply the review file's ticks and publish approved drafts that are due"
    )
    publish.add_argument(
        "--simular", action="store_true", help="print what would happen, change nothing"
    )
    publish.set_defaults(run=publicar)

    args = parser.parse_args(argv)
    args.transport = transport
    return args.run(args, config or config_module.load())


if __name__ == "__main__":
    sys.exit(main())
