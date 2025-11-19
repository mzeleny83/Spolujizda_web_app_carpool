#!/usr/bin/env python3
"""
Unifies the Spolujizda web (spolujizda.db) and mobile (spolujizda_enhanced.db)
SQLite databases into a single database that keeps the web schema as baseline
while adding the fields/tables required by the mobile backend.

Usage:
    python merge_databases.py \
        --web-db spolujizda.db \
        --mobile-db spolujizda_enhanced.db \
        --output-db spolujizda_unified.db
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import shutil
import sqlite3
from collections import defaultdict
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple

DEFAULT_WEB_DB = Path("spolujizda.db")
DEFAULT_MOBILE_DB = Path("spolujizda_enhanced.db")
DEFAULT_OUTPUT_DB = Path("spolujizda_unified.db")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--web-db",
        type=Path,
        default=DEFAULT_WEB_DB,
        help="Path to the source (web) database that defines the base schema.",
    )
    parser.add_argument(
        "--mobile-db",
        type=Path,
        default=DEFAULT_MOBILE_DB,
        help="Path to the mobile/enhanced database whose data should be merged.",
    )
    parser.add_argument(
        "--output-db",
        type=Path,
        default=DEFAULT_OUTPUT_DB,
        help="Path to the resulting unified database.",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite the output database if it already exists.",
    )
    return parser.parse_args()


def copy_base_database(web_db: Path, output_db: Path, allow_overwrite: bool) -> None:
    if not web_db.exists():
        raise FileNotFoundError(f"Base web database '{web_db}' not found.")

    if output_db.exists():
        if not allow_overwrite:
            raise FileExistsError(
                f"Output database '{output_db}' already exists. "
                "Use --force to overwrite."
            )
        output_db.unlink()

    shutil.copy2(web_db, output_db)


def open_conn(path: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = OFF")
    return conn


def ensure_columns(
    conn: sqlite3.Connection, table: str, columns: Dict[str, str]
) -> None:
    cursor = conn.execute(f"PRAGMA table_info({table})")
    existing = {row["name"] for row in cursor.fetchall()}
    for column, ddl in columns.items():
        if column not in existing:
            conn.execute(f"ALTER TABLE {table} ADD COLUMN {ddl}")


def ensure_table(conn: sqlite3.Connection, ddl: str) -> None:
    conn.execute(ddl)


def ensure_schema(conn: sqlite3.Connection) -> None:
    # Additional user columns needed by the mobile backend
    ensure_columns(
        conn,
        "users",
        {
            "phone_verified": "phone_verified BOOLEAN DEFAULT 0",
            "profile_photo": "profile_photo TEXT",
            "id_verified": "id_verified BOOLEAN DEFAULT 0",
            "license_verified": "license_verified BOOLEAN DEFAULT 0",
        },
    )

    # Additional ride columns required by the mobile backend
    ensure_columns(
        conn,
        "rides",
        {
            "from_lat": "from_lat REAL",
            "from_lng": "from_lng REAL",
            "to_lat": "to_lat REAL",
            "to_lng": "to_lng REAL",
            "price": "price REAL",
            "description": "description TEXT",
            "car_model": "car_model TEXT",
            "car_color": "car_color TEXT",
            "smoking_allowed": "smoking_allowed BOOLEAN DEFAULT 0",
            "pets_allowed": "pets_allowed BOOLEAN DEFAULT 0",
            "recurring": "recurring BOOLEAN DEFAULT 0",
            "recurring_days": "recurring_days TEXT",
            "status": "status TEXT DEFAULT 'active'",
        },
    )

    # Extra tables that only exist in the mobile backend
    ensure_table(
        conn,
        """
        CREATE TABLE IF NOT EXISTS bookings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ride_id INTEGER NOT NULL,
            passenger_id INTEGER NOT NULL,
            seats_booked INTEGER DEFAULT 1,
            status TEXT DEFAULT 'pending',
            payment_status TEXT DEFAULT 'unpaid',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (ride_id) REFERENCES rides (id),
            FOREIGN KEY (passenger_id) REFERENCES users (id)
        )
        """,
    )

    ensure_columns(
        conn,
        "payments",
        {
            "booking_id": "booking_id INTEGER",
            "currency": "currency TEXT DEFAULT 'CZK'",
            "payment_method": "payment_method TEXT",
            "transaction_id": "transaction_id TEXT",
        },
    )

    ensure_table(
        conn,
        """
        CREATE TABLE IF NOT EXISTS favorite_routes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            from_location TEXT NOT NULL,
            to_location TEXT NOT NULL,
            from_lat REAL,
            from_lng REAL,
            to_lat REAL,
            to_lng REAL,
            name TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
        """,
    )

    ensure_table(
        conn,
        """
        CREATE TABLE IF NOT EXISTS chat_messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ride_id INTEGER NOT NULL,
            sender_id INTEGER,
            sender_name TEXT NOT NULL,
            message TEXT NOT NULL,
            message_type TEXT DEFAULT 'text',
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (ride_id) REFERENCES rides (id),
            FOREIGN KEY (sender_id) REFERENCES users (id)
        )
        """,
    )

    conn.commit()


def normalize_phone(phone: Optional[str]) -> str:
    if not phone:
        return ""
    digits = "".join(ch for ch in phone if ch.isdigit())
    if digits.startswith("420") and len(digits) > 9:
        digits = digits[3:]
    return digits


def row_value(row: sqlite3.Row, key: str, default=None):
    return row[key] if key in row.keys() else default


def to_iso(value) -> Optional[str]:
    if value is None:
        return None
    if isinstance(value, str):
        return value
    if isinstance(value, (dt.date, dt.datetime)):
        return value.isoformat()
    return str(value)


def merge_users(
    dest_conn: sqlite3.Connection, src_conn: sqlite3.Connection
) -> Tuple[Dict[int, int], Dict[str, int], Dict[str, int]]:
    phone_to_dest: Dict[str, int] = {}
    email_to_dest: Dict[str, int] = {}
    phone_cursor = dest_conn.execute("SELECT id, phone, email FROM users")
    for row in phone_cursor.fetchall():
        phone_to_dest[normalize_phone(row["phone"])] = row["id"]
        if row["email"]:
            email_to_dest[row["email"].strip().lower()] = row["id"]

    src_to_dest: Dict[int, int] = {}
    inserted = updated = 0

    user_cursor = src_conn.execute("SELECT * FROM users")
    for user in user_cursor.fetchall():
        norm_phone = normalize_phone(row_value(user, "phone"))
        email = row_value(user, "email")
        email_key = email.strip().lower() if email else None
        dest_id = phone_to_dest.get(norm_phone)
        if not dest_id and email_key:
            dest_id = email_to_dest.get(email_key)

        if dest_id:
            updates = {}
            dest_row = dest_conn.execute(
                "SELECT * FROM users WHERE id = ?", (dest_id,)
            ).fetchone()
            if email and not dest_row["email"]:
                updates["email"] = email
            if row_value(user, "bio") and not dest_row["bio"]:
                updates["bio"] = row_value(user, "bio")
            if row_value(user, "home_city") and not dest_row["home_city"]:
                updates["home_city"] = row_value(user, "home_city")
            phone_verified = 1 if row_value(user, "phone_verified") else 0
            id_verified = 1 if row_value(user, "id_verified") else 0
            license_verified = 1 if row_value(user, "license_verified") else 0
            if phone_verified and dest_row["phone_verified"] != phone_verified:
                updates["phone_verified"] = phone_verified
            if id_verified and dest_row["id_verified"] != id_verified:
                updates["id_verified"] = id_verified
            if license_verified and dest_row["license_verified"] != license_verified:
                updates["license_verified"] = license_verified
            if row_value(user, "profile_photo") and not dest_row["profile_photo"]:
                updates["profile_photo"] = row_value(user, "profile_photo")

            if updates:
                assignments = ", ".join(f"{col} = ?" for col in updates)
                dest_conn.execute(
                    f"UPDATE users SET {assignments} WHERE id = ?",
                    (*updates.values(), dest_id),
                )
                updated += 1
        else:
            created_at = to_iso(row_value(user, "created_at")) or to_iso(dt.datetime.now())
            dest_conn.execute(
                """
                INSERT INTO users (
                    name, phone, email, password_hash, rating, total_rides,
                    verified, created_at, last_active, bio, home_city, paypal_email,
                    phone_verified, profile_photo, id_verified, license_verified
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    row_value(user, "name"),
                    norm_phone,
                    email,
                    row_value(user, "password_hash"),
                    row_value(user, "rating", 5.0),
                    row_value(user, "total_rides", 0),
                    1 if row_value(user, "phone_verified") else 0,
                    created_at,
                    created_at,
                    row_value(user, "bio"),
                    row_value(user, "home_city"),
                    None,
                    1 if row_value(user, "phone_verified") else 0,
                    row_value(user, "profile_photo"),
                    1 if row_value(user, "id_verified") else 0,
                    1 if row_value(user, "license_verified") else 0,
                ),
            )
            dest_id = dest_conn.execute("SELECT last_insert_rowid()").fetchone()[0]
            phone_to_dest[norm_phone] = dest_id
            if email_key:
                email_to_dest[email_key] = dest_id
            inserted += 1

        src_to_dest[user["id"]] = dest_id

    dest_conn.commit()
    return src_to_dest, phone_to_dest, {"inserted": inserted, "updated": updated}


def merge_rides(
    dest_conn: sqlite3.Connection,
    src_conn: sqlite3.Connection,
    src_to_dest_users: Dict[int, int],
) -> Dict[str, int]:
    inserted = skipped = 0
    ride_cursor = src_conn.execute("SELECT * FROM rides")
    for ride in ride_cursor.fetchall():
        source_driver_id = ride["driver_id"]
        dest_driver_id = src_to_dest_users.get(source_driver_id)
        if not dest_driver_id:
            skipped += 1
            continue

        departure_time = to_iso(row_value(ride, "departure_time"))
        existing = dest_conn.execute(
            """
            SELECT id FROM rides
            WHERE user_id = ? AND from_location = ? AND to_location = ?
                  AND departure_time = ?
            """,
            (
                dest_driver_id,
                row_value(ride, "from_location"),
                row_value(ride, "to_location"),
                departure_time,
            ),
        ).fetchone()

        if existing:
            skipped += 1
            continue

        created_at = to_iso(row_value(ride, "created_at")) or departure_time
        dest_conn.execute(
            """
            INSERT INTO rides (
                user_id, from_location, to_location, departure_time,
                available_seats, price_per_person, price, description,
                route_waypoints, created_at, from_lat, from_lng, to_lat,
                to_lng, car_model, car_color, smoking_allowed, pets_allowed,
                recurring, recurring_days, status
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                dest_driver_id,
                row_value(ride, "from_location"),
                row_value(ride, "to_location"),
                departure_time,
                row_value(ride, "available_seats", 1),
                row_value(ride, "price"),
                row_value(ride, "price"),
                row_value(ride, "description"),
                json.dumps(
                    {
                        "recurring": row_value(ride, "recurring"),
                        "recurring_days": row_value(ride, "recurring_days"),
                    }
                ),
                created_at,
                row_value(ride, "from_lat"),
                row_value(ride, "from_lng"),
                row_value(ride, "to_lat"),
                row_value(ride, "to_lng"),
                row_value(ride, "car_model"),
                row_value(ride, "car_color"),
                1 if row_value(ride, "smoking_allowed") else 0,
                1 if row_value(ride, "pets_allowed") else 0,
                1 if row_value(ride, "recurring") else 0,
                row_value(ride, "recurring_days"),
                row_value(ride, "status") or "active",
            ),
        )
        inserted += 1

    dest_conn.commit()
    return {"inserted": inserted, "skipped": skipped}


def main() -> None:
    args = parse_args()

    copy_base_database(args.web_db, args.output_db, args.force)
    dest_conn = open_conn(args.output_db)
    src_conn = open_conn(args.mobile_db)

    ensure_schema(dest_conn)
    user_map, _, user_stats = merge_users(dest_conn, src_conn)
    ride_stats = merge_rides(dest_conn, src_conn, user_map)

    dest_conn.close()
    src_conn.close()

    print(
        json.dumps(
            {
                "output_db": str(args.output_db),
                "user_stats": user_stats,
                "ride_stats": ride_stats,
            },
            indent=2,
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
