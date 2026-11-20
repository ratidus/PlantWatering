"""Автономне локальне сховище LocalStorage на базі SQLite (Local-first)."""

import sqlite3
from datetime import date, datetime
from typing import List

from src.models import Plant, WateringEvent, WateringStatus


class LocalStorage:
    """Транзакційне збереження колекції рослин та історії поливів у SQLite."""

    def __init__(self, db_path: str = "plant_watering.db") -> None:
        self.db_path = db_path
        self._init_schema()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.execute("PRAGMA foreign_keys = ON;")
        return conn

    def _init_schema(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS plants (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    species_id INTEGER,
                    base_interval_days INTEGER NOT NULL,
                    last_watered_date TEXT NOT NULL,
                    next_watering_date TEXT NOT NULL,
                    status TEXT NOT NULL
                );
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS watering_events (
                    event_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    plant_id INTEGER NOT NULL,
                    watered_timestamp TEXT NOT NULL,
                    applied_k_season REAL NOT NULL,
                    calculated_next_date TEXT NOT NULL,
                    FOREIGN KEY (plant_id) REFERENCES plants(id) ON DELETE CASCADE
                );
                """
            )

    def load_plants(self) -> List[Plant]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT id, name, species_id, base_interval_days,
                       last_watered_date, next_watering_date, status
                FROM plants
                ORDER BY next_watering_date ASC;
                """
            ).fetchall()
        return [
            Plant(
                id=r[0],
                name=r[1],
                species_id=r[2],
                base_interval_days=r[3],
                last_watered_date=date.fromisoformat(r[4]),
                next_watering_date=date.fromisoformat(r[5]),
                status=WateringStatus(r[6]),
            )
            for r in rows
        ]

    def save_plant(self, plant: Plant) -> Plant:
        with self._connect() as conn:
            if plant.id is None:
                cur = conn.execute(
                    """
                    INSERT INTO plants (
                        name, species_id, base_interval_days,
                        last_watered_date, next_watering_date, status
                    ) VALUES (?, ?, ?, ?, ?, ?);
                    """,
                    (
                        plant.name,
                        plant.species_id,
                        plant.base_interval_days,
                        plant.last_watered_date.isoformat(),
                        plant.next_watering_date.isoformat(),
                        plant.status.value,
                    ),
                )
                plant.id = cur.lastrowid
            else:
                conn.execute(
                    """
                    UPDATE plants
                    SET name = ?, species_id = ?, base_interval_days = ?,
                        last_watered_date = ?, next_watering_date = ?, status = ?
                    WHERE id = ?;
                    """,
                    (
                        plant.name,
                        plant.species_id,
                        plant.base_interval_days,
                        plant.last_watered_date.isoformat(),
                        plant.next_watering_date.isoformat(),
                        plant.status.value,
                        plant.id,
                    ),
                )
        return plant

    def delete_plant(self, plant_id: int) -> None:
        with self._connect() as conn:
            conn.execute("DELETE FROM plants WHERE id = ?;", (plant_id,))

    def append_event(self, event: WateringEvent) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO watering_events (
                    plant_id, watered_timestamp, applied_k_season, calculated_next_date
                ) VALUES (?, ?, ?, ?);
                """,
                (
                    event.plant_id,
                    event.watered_timestamp.isoformat(),
                    event.applied_k_season,
                    event.calculated_next_date.isoformat(),
                ),
            )

    def load_history(self, plant_id: int | None = None) -> List[WateringEvent]:
        with self._connect() as conn:
            if plant_id is None:
                rows = conn.execute(
                    """
                    SELECT event_id, plant_id, watered_timestamp, applied_k_season, calculated_next_date
                    FROM watering_events
                    ORDER BY watered_timestamp DESC;
                    """
                ).fetchall()
            else:
                rows = conn.execute(
                    """
                    SELECT event_id, plant_id, watered_timestamp, applied_k_season, calculated_next_date
                    FROM watering_events
                    WHERE plant_id = ?
                    ORDER BY watered_timestamp DESC;
                    """,
                    (plant_id,),
                ).fetchall()
        return [
            WateringEvent(
                event_id=r[0],
                plant_id=r[1],
                watered_timestamp=datetime.fromisoformat(r[2]),
                applied_k_season=r[3],
                calculated_next_date=date.fromisoformat(r[4]),
            )
            for r in rows
        ]
