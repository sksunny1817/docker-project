from __future__ import annotations

from typing import Generator

from fastapi import Depends, FastAPI, HTTPException, Query
from sqlalchemy.orm import Session

from database import Base, engine, get_db
from models.customer import Customer
from services.ingestion import ingest_customers

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Customer Pipeline Service", version="1.0.0")


@app.get("/api/health")
def health_check():
    return {"status": "healthy", "service": "pipeline-service"}


@app.post("/api/ingest")
def ingest(db: Session = Depends(get_db)):
    try:
        processed = ingest_customers(db)
        return {"status": "success", "records_processed": processed}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Ingestion failed: {exc}") from exc


@app.get("/api/customers")
def get_customers(
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db),
):
    total = db.query(Customer).count()
    offset = (page - 1) * limit
    records = (
        db.query(Customer)
        .order_by(Customer.customer_id)
        .offset(offset)
        .limit(limit)
        .all()
    )

    data = [
        {
            "customer_id": record.customer_id,
            "first_name": record.first_name,
            "last_name": record.last_name,
            "email": record.email,
            "phone": record.phone,
            "address": record.address,
            "date_of_birth": record.date_of_birth.isoformat() if record.date_of_birth else None,
            "account_balance": float(record.account_balance) if record.account_balance is not None else None,
            "created_at": record.created_at.isoformat() if record.created_at else None,
        }
        for record in records
    ]

    return {"data": data, "total": total, "page": page, "limit": limit}


@app.get("/api/customers/{customer_id}")
def get_customer(customer_id: str, db: Session = Depends(get_db)):
    record = db.query(Customer).filter(Customer.customer_id == customer_id).first()
    if not record:
        raise HTTPException(status_code=404, detail=f"Customer {customer_id} not found")

    return {
        "customer_id": record.customer_id,
        "first_name": record.first_name,
        "last_name": record.last_name,
        "email": record.email,
        "phone": record.phone,
        "address": record.address,
        "date_of_birth": record.date_of_birth.isoformat() if record.date_of_birth else None,
        "account_balance": float(record.account_balance) if record.account_balance is not None else None,
        "created_at": record.created_at.isoformat() if record.created_at else None,
    }
