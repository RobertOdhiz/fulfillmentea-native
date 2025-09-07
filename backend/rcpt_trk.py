import sqlite3
import random

DB_PATH = "./backend/db.sqlite3"

def column_exists(cursor, table, column):
    cursor.execute(f"PRAGMA table_info({table});")
    return any(row[1] == column for row in cursor.fetchall())

def generate_code(prefix: str) -> str:
    """Generate a code like TRK-ABCDE or RCPT-ABCDE using safe characters."""
    safe_chars = "ABCDEFGHJKMNPQRSTUVWXYZ123456789"  # no O, 0, I, L
    suffix = "".join(random.choices(safe_chars, k=5))
    return f"{prefix}-{suffix}"

def migrate():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    # 1. Ensure tracking_number column exists in parcels
    if not column_exists(cur, "parcels", "tracking_number"):
        cur.execute("ALTER TABLE parcels ADD COLUMN tracking_number TEXT;")

    # 2. Ensure receipt_number column exists in receipts
    if not column_exists(cur, "receipts", "receipt_number"):
        cur.execute("ALTER TABLE receipts ADD COLUMN receipt_number TEXT;")

    conn.commit()

    # 3. Update parcels with new tracking numbers
    cur.execute("SELECT id FROM parcels;")
    parcels = cur.fetchall()
    for (parcel_id,) in parcels:
        tracking_number = generate_code("TRK")
        cur.execute(
            "UPDATE parcels SET tracking_number=? WHERE id=?",
            (tracking_number, parcel_id)
        )

    # 4. Update receipts with new receipt numbers
    cur.execute("SELECT id FROM receipts;")
    receipts = cur.fetchall()
    for (receipt_id,) in receipts:
        receipt_number = generate_code("RCPT")
        cur.execute(
            "UPDATE receipts SET receipt_number=? WHERE id=?",
            (receipt_number, receipt_id)
        )

    conn.commit()
    conn.close()
    print("✅ Migration complete! Tracking and receipt numbers updated.")

if __name__ == "__main__":
    migrate()
