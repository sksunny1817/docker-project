from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from flask import Flask, jsonify, request

app = Flask(__name__)
DATA_FILE = Path(__file__).resolve().parent / "data" / "customers.json"


def load_customers() -> list[dict[str, Any]]:
    with DATA_FILE.open("r", encoding="utf-8") as file:
        return json.load(file)


@app.get("/api/health")
def health_check():
    return jsonify({"status": "healthy", "service": "mock-server"}), 200


@app.get("/api/customers")
def get_customers():
    try:
        page = max(int(request.args.get("page", 1)), 1)
        limit = max(int(request.args.get("limit", 10)), 1)
    except ValueError:
        return jsonify({"detail": "page and limit must be integers"}), 400

    customers = load_customers()
    total = len(customers)
    start = (page - 1) * limit
    end = start + limit
    paginated = customers[start:end]

    return jsonify(
        {
            "data": paginated,
            "total": total,
            "page": page,
            "limit": limit,
        }
    )


@app.get("/api/customers/<customer_id>")
def get_customer(customer_id: str):
    customers = load_customers()
    customer = next((item for item in customers if item["customer_id"] == customer_id), None)
    if not customer:
        return jsonify({"detail": f"Customer {customer_id} not found"}), 404
    return jsonify(customer), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
