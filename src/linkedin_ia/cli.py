"""The `linkedin` command: coletar, checar, fila."""

import argparse
import sys
from datetime import date, datetime

from linkedin_ia import config as config_module
from linkedin_ia import digest, state


def coletar(args: argparse.Namespace, config: config_module.Config) -> int:
    started = datetime.now().astimezone()
    since = state.window_start(config, started, args.desde)
    path = digest.write(digest.collect(config, since, started), config)
    state.record_run(config, started)
    print(path)
    return 0


def main(argv: list[str] | None = None, config: config_module.Config | None = None) -> int:
    parser = argparse.ArgumentParser(prog="linkedin", description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)

    collect = commands.add_parser("coletar", help="write the digest of the window")
    collect.add_argument("--desde", type=date.fromisoformat, metavar="AAAA-MM-DD")
    collect.set_defaults(run=coletar)

    args = parser.parse_args(argv)
    return args.run(args, config or config_module.load())


if __name__ == "__main__":
    sys.exit(main())
