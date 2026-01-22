"""Minimal CLI entrypoint for the pipeline."""

import argparse
import sys

from clinical_trial_pipeline.common.logging import setup_logging
from clinical_trial_pipeline.load.ingestion import IngestService


def cmd_ingest(args: argparse.Namespace) -> int:
    """Run ingestion command."""
    setup_logging()

    service = IngestService(
        db_path=args.db_path,
        page_size=args.page_size,
    )

    result = service.run(max_studies=args.max_studies)

    print(f"\nIngestion complete:")
    print(f"  Inserted: {result.inserted}")
    print(f"  Skipped:  {result.skipped}")
    print(f"  Pages:    {result.pages}")
    print(f"  Errors:   {len(result.errors)}")

    return 1 if result.errors else 0


def main() -> int:
    """CLI entrypoint."""
    parser = argparse.ArgumentParser(
        prog="clinical_trial_pipeline",
        description="Clinical Trial Data Pipeline",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # ingest command
    ingest_parser = subparsers.add_parser("ingest", help="Ingest data from API")
    ingest_parser.add_argument(
        "--db-path",
        default="data/clinical_trials.duckdb",
        help="Path to DuckDB database (default: data/clinical_trials.duckdb)",
    )
    ingest_parser.add_argument(
        "--max-studies",
        type=int,
        default=None,
        help="Maximum number of studies to ingest",
    )
    ingest_parser.add_argument(
        "--page-size",
        type=int,
        default=100,
        help="Number of studies per API request (default: 100)",
    )
    ingest_parser.set_defaults(func=cmd_ingest)

    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
