"""Доменні моделі даних для ПЗ PlantWatering (згідно з діаграмою класів ЛР №3)."""

from dataclasses import dataclass
from datetime import date, datetime
from enum import Enum
from typing import List, Optional


class WateringStatus(Enum):
    """Статус пріоритету поливу рослини у черзі екрана «Сьогодні»."""

    OVERDUE = "Терміново"
    TODAY = "Сьогодні"
    PLANNED = "Заплановано"


@dataclass(frozen=True)
class Species:
    """Довідникова картка виду кімнатної рослини."""

    species_id: int
    title: str
    light_level: str
    default_interval_days: int
    misting_sensitive: bool

    def to_plant_template(self, last_watered: date, next_watering: date) -> "Plant":
        return Plant(
            id=None,
            name=self.title,
            species_id=self.species_id,
            base_interval_days=self.default_interval_days,
            last_watered_date=last_watered,
            next_watering_date=next_watering,
            status=WateringStatus.PLANNED,
        )


@dataclass(frozen=True)
class SeasonRule:
    """Правило сезонного коефіцієнта поливу K_season."""

    season_id: int
    season_name: str
    months: List[int]
    k_season_multiplier: float

    def matches_date(self, target_date: date) -> bool:
        return target_date.month in self.months


@dataclass
class Plant:
    """Екземпляр кімнатної рослини у колекції користувача «Мої рослини»."""

    id: Optional[int]
    name: str
    base_interval_days: int
    last_watered_date: date
    next_watering_date: date
    status: WateringStatus = WateringStatus.PLANNED
    species_id: Optional[int] = None

    def validate_interval(self) -> bool:
        return 1 <= self.base_interval_days <= 60

    def update_watering(self, watered_date: date, next_date: date, status: WateringStatus) -> None:
        self.last_watered_date = watered_date
        self.next_watering_date = next_date
        self.status = status


@dataclass(frozen=True)
class WateringEvent:
    """Запис локального журналу історії виконаних поливів."""

    event_id: Optional[int]
    plant_id: int
    watered_timestamp: datetime
    applied_k_season: float
    calculated_next_date: date

    def format_log_entry(self) -> str:
        ts = self.watered_timestamp.strftime("%Y-%m-%d %H:%M")
        return (
            f"[{ts}] Рослина #{self.plant_id}: полито "
            f"(K_season={self.applied_k_season:.2f}), наступний полив: {self.calculated_next_date.isoformat()}"
        )
