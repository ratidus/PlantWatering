"""Обчислювальне ядро PlantWatering: сезонний розрахунок дат поливу та статусів."""

import math
from datetime import date, timedelta
from typing import List, Optional

from src.models import SeasonRule, WateringStatus

DEFAULT_SEASON_RULES: List[SeasonRule] = [
    SeasonRule(1, "Зима", [12, 1, 2], 1.5),
    SeasonRule(2, "Весна", [3, 4, 5], 1.25),
    SeasonRule(3, "Літо", [6, 7, 8], 1.0),
    SeasonRule(4, "Осінь", [9, 10, 11], 1.25),
]


class WateringCalculator:
    """Обчислює планову дату наступного поливу та пріоритетний статус."""

    def __init__(self, season_rules: Optional[List[SeasonRule]] = None) -> None:
        self.season_rules = season_rules or DEFAULT_SEASON_RULES

    def get_active_rule(self, target_date: date) -> SeasonRule:
        for rule in self.season_rules:
            if rule.matches_date(target_date):
                return rule
        return self.season_rules[0]

    def calculate_next_date(
        self,
        last_watered: date,
        base_interval_days: int,
        rule: Optional[SeasonRule] = None,
    ) -> date:
        """Формула: Date_next = Date_last + ceil(BaseInterval * K_season)."""
        if not (1 <= base_interval_days <= 60):
            raise ValueError("Базовий інтервал поливу має бути в межах від 1 до 60 діб.")
        active_rule = rule or self.get_active_rule(last_watered)
        adjusted_days = math.ceil(base_interval_days * active_rule.k_season_multiplier)
        return last_watered + timedelta(days=adjusted_days)

    @staticmethod
    def determine_status(next_watering_date: date, today: Optional[date] = None) -> WateringStatus:
        """Визначає статус за різницею днів ΔD = Date_next - Date_current."""
        current = today or date.today()
        delta_days = (next_watering_date - current).days
        if delta_days < 0:
            return WateringStatus.OVERDUE
        if delta_days == 0:
            return WateringStatus.TODAY
        return WateringStatus.PLANNED
