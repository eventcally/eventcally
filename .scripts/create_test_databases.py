#!/usr/bin/env python3
"""Create (or recreate) the per-group databases used by the parallel test runner.

Run against an admin connection with CREATEDB privileges (the compose ``db`` service's
maintenance database, not a per-group test database). For each group number N it
terminates any lingering backends on ``<prefix>_N``, drops it if present, and recreates it
from ``template_postgis`` -- the template the official ``postgis/postgis`` image seeds on
first init with PostGIS already installed, so no per-database ``CREATE EXTENSION`` is
needed. Falls back to a plain ``CREATE DATABASE`` + ``CREATE EXTENSION`` when that template
is absent, e.g. for a ``TEST_DB_IMAGE`` override that isn't the official postgis image.

There is no ``psql`` in the test image (see ``Dockerfile``), so this talks to Postgres
directly via psycopg2. Identifiers are always built as ``<prefix>_<n>`` and passed through
``psycopg2.sql.Identifier``, never interpolated into SQL as strings.

Guard rail: refuses to run if the admin connection's own database looks like one of the
per-group databases it would drop -- that would mean it was pointed at a test database
instead of the shared maintenance database.
"""

import argparse
import os
import sys

import psycopg2
from psycopg2 import sql
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT, make_dsn, parse_dsn

DEFAULT_PREFIX = "eventcally_tests"
TEMPLATE_DATABASE = "template_postgis"


def database_exists(cur, name):
    cur.execute("SELECT 1 FROM pg_database WHERE datname = %s", (name,))
    return cur.fetchone() is not None


def terminate_backends(cur, name):
    cur.execute(
        "SELECT pg_terminate_backend(pid) FROM pg_stat_activity"
        " WHERE datname = %s AND pid <> pg_backend_pid()",
        (name,),
    )


def recreate_database(admin_url, cur, name):
    if database_exists(cur, name):
        terminate_backends(cur, name)
        cur.execute(sql.SQL("DROP DATABASE IF EXISTS {}").format(sql.Identifier(name)))

    if database_exists(cur, TEMPLATE_DATABASE):
        cur.execute(
            sql.SQL("CREATE DATABASE {} TEMPLATE {}").format(
                sql.Identifier(name), sql.Identifier(TEMPLATE_DATABASE)
            )
        )
        return

    cur.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(name)))
    with psycopg2.connect(make_dsn(admin_url, dbname=name)) as conn:
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        with conn.cursor() as ext_cur:
            ext_cur.execute("CREATE EXTENSION IF NOT EXISTS postgis")


def parse_args(argv):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--admin-url",
        default=os.environ.get("TEST_DB_ADMIN_URL"),
        help="Admin DSN with CREATEDB privileges (default: $TEST_DB_ADMIN_URL)",
    )
    parser.add_argument(
        "--splits",
        type=int,
        help="Create groups 1..N (mutually exclusive with --groups)",
    )
    parser.add_argument(
        "--groups",
        type=int,
        nargs="+",
        help="Explicit group numbers to create instead of --splits",
    )
    parser.add_argument(
        "--prefix",
        default=DEFAULT_PREFIX,
        help=f"Database name prefix (default: {DEFAULT_PREFIX})",
    )
    args = parser.parse_args(argv)

    if not args.admin_url:
        parser.error("--admin-url or $TEST_DB_ADMIN_URL is required")
    if not args.splits and not args.groups:
        parser.error("one of --splits or --groups is required")
    if args.splits and args.groups:
        parser.error("--splits and --groups are mutually exclusive")

    return args


def main(argv=None):
    args = parse_args(argv)
    groups = args.groups or range(1, args.splits + 1)

    admin_dbname = parse_dsn(args.admin_url).get("dbname", "")
    if admin_dbname.startswith(args.prefix):
        print(
            f"refusing to run: admin database {admin_dbname!r} looks like a per-group"
            " test database itself, not the shared maintenance database",
            file=sys.stderr,
        )
        return 1

    conn = psycopg2.connect(args.admin_url)
    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    try:
        with conn.cursor() as cur:
            for group in groups:
                name = f"{args.prefix}_{group}"
                recreate_database(args.admin_url, cur, name)
                print(f"created {name}")
    finally:
        conn.close()

    return 0


if __name__ == "__main__":
    sys.exit(main())
