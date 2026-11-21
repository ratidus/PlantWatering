"""Сервіс локальних сповіщень без підключення до мережі."""

from typing import List
from src.models import Plant, WateringStatus


class NotificationService:
    """Формує офлайн-нагадування для прострочених і сьогоднішніх завдань."""

    def __init__(self, is_enabled: bool = True, reminder_hour: int = 9) -> None:
        self.is_enabled = is_enabled
        self.reminder_hour = reminder_hour

    def collect_due_alerts(self, plants: List[Plant]) -> List[str]:
        if not self.is_enabled:
            return []
        alerts: List[str] = []
        for p in plants:
            if p.status == WateringStatus.OVERDUE:
                alerts.append(f"Терміново: рослина «{p.name}» прострочена (дедлайн {p.next_watering_date}).")
            elif p.status == WateringStatus.TODAY:
                alerts.append(f"Сьогодні потрібно полити: «{p.name}».")
        return alerts
