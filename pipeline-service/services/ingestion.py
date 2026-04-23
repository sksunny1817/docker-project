from __future__ import annotations

import os
from datetime import date, datetime
from decimal import Decimal
from typing import Any

import dlt
import requests
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from models.customer import Customer

MOCK_SERVER_BASE_URL = os.getenv("MOCK_SERVER_BASE_URL", "http://localhost:5000")
PAGE_SIZE = 10


def _parse_customer(record: dict[str, Any]) -> dict[str, Any]:
    dob = record.get("date_of_birth")
    created = record.get("created_at")

    return {
        "customer_id": record["customer_id"],
        "first_name": record["first_name"],
        "last_name": record["last_name"],
        "email": record["email"],
        "phone": record.get("phone"),
        "address": record.get("address"),
        "date_of_birth": date.fromisoformat(dob) if dob else None,
        "account_balance": Decimal(str(record.get("account_balance", 0))),
        "created_at": datetime.fromisoformat(created) if created else None,
    }


def fetch_all_customers() -> list[dict[str, Any]]:
    customers: list[dict[str, Any]] = []
    page = 1

    while True:
        response = requests.get(
            f"{MOCK_SERVER_BASE_URL}/api/customers",
            params={"page": page, "limit": PAGE_SIZE},
            timeout=30,
        )
        response.raise_for_status()
        payload = response.json()
        data = payload.get("data", [])
        customers.extend(data)

        total = payload.get("total", 0)
        if len(customers) >= total or not data:
            break
        page += 1

    return customers


def run_dlt_pipeline(customers: list[dict[str, Any]]) -> None:
    pipeline = dlt.pipeline(
        pipeline_name="customer_ingestion_pipeline",
        destination="postgres",
        dataset_name="public",
    )
    pipeline.run(customers, table_name="customers", write_disposition="append")


def upsert_customers(db: Session, customers: list[dict[str, Any]]) -> int:
    parsed_customers = [_parse_customer(customer) for customer in customers]

    if not parsed_customers:
        return 0

    statement = insert(Customer).values(parsed_customers)
    update_columns = {
        "first_name": statement.excluded.first_name,
        "last_name": statement.excluded.last_name,
        "email": statement.excluded.email,
        "phone": statement.excluded.phone,
        "address": statement.excluded.address,
        "date_of_birth": statement.excluded.date_of_birth,
        "account_balance": statement.excluded.account_balance,
        "created_at": statement.excluded.created_at,
    }

    statement = statement.on_conflict_do_update(
        index_elements=[Customer.customer_id],
        set_=update_columns,
    )

    db.execute(statement)
    db.commit()
    return len(parsed_customers)


def ingest_customers(db: Session) -> int:
    customers = fetch_all_customers()
    run_dlt_pipeline(customers)
    return upsert_customers(db, customers)
