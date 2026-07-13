from __future__ import annotations

import argparse
from pathlib import Path

from signalops.seed_data import seed_records
from signalops.storage import make_account_store


ROOT = Path(__file__).resolve().parent
LOCAL_DB_PATH = ROOT / "data" / "signalops_crm.sqlite"


def main() -> None:
    parser = argparse.ArgumentParser(description="Seed the 10 manually researched Perk-fit accounts.")
    parser.add_argument(
        "--local-sqlite",
        action="store_true",
        help="Kept for backward compatibility; seeding uses local SQLite for the MVP.",
    )
    parser.parse_args()

    store = make_account_store(LOCAL_DB_PATH)
    records = seed_records()
    for record in records:
        store.upsert_account(record)

    print(f"Seeded {len(records)} accounts into local SQLite.")


if __name__ == "__main__":
    main()
