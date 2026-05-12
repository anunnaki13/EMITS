from typing import Optional


def build_rekap_query(
    *,
    search: Optional[str],
    search_fields: list[str],
    supplier: Optional[str],
    date_from: Optional[str],
    date_to: Optional[str],
    date_field: str,
    supplier_field: str = "suppliers",
) -> dict:
    conditions = []

    if search:
        conditions.append({
            "$or": [
                {field: {"$regex": search, "$options": "i"}}
                for field in search_fields
            ]
        })

    if supplier and supplier != "all":
        conditions.append({supplier_field: {"$regex": supplier, "$options": "i"}})

    if date_from or date_to:
        date_filter = {}
        if date_from:
            date_filter["$gte"] = date_from
        if date_to:
            date_filter["$lte"] = f"{date_to}T23:59:59"
        conditions.append({date_field: date_filter})

    if not conditions:
        return {}
    if len(conditions) == 1:
        return conditions[0]
    return {"$and": conditions}
