"""Центральний координатор TaskDispatcher для ПЗ PlantWatering."""

import csv
from datetime import date, datetime
from typing import List, Optional

from src.calculator import WateringCalculator
from src.catalog import PlantCatalog
from src.models import Plant, Species, WateringEvent, WateringStatus
from src.notifications import NotificationService
from src.storage import LocalStorage

STATUS_PRIORITY = {
    WateringStatus.OVERDUE: 0,
    WateringStatus.TODAY: 1,
    WateringStatus.PLANNED: 2,
}


class TaskDispatcher:
    """Координує чергу екрана «Сьогодні», каталог, калькулятор дат і сховище."""

    def __init__(
        self,
        storage: Optional[LocalStorage] = None,
        catalog: Optional[PlantCatalog] = None,
        calculator: Optional[WateringCalculator] = None,
        notifications: Optional[NotificationService] = None,
    ) -> None:
        self.storage = storage or LocalStorage()
        self.catalog = catalog or PlantCatalog()
        self.calculator = calculator or WateringCalculator()
        self.notifications = notifications or NotificationService()

    def load_today_queue(self, today: Optional[date] = None) -> List[Plant]:
        current = today or date.today()
        plants = self.storage.load_plants()
        for p in plants:
            p.status = self.calculator.determine_status(p.next_watering_date, current)
        plants.sort(key=lambda p: (STATUS_PRIORITY[p.status], p.next_watering_date, p.name))
        return plants

    def add_plant(
        self,
        name: str,
        base_interval_days: int,
        last_watered_date: date,
        species_id: Optional[int] = None,
        today: Optional[date] = None,
    ) -> Plant:
        clean_name = name.strip()
        if not clean_name:
            raise ValueError("Назва рослини не може бути порожньою.")
        current = today or date.today()
        if last_watered_date > current:
            raise ValueError("Дата останнього поливу не може бути в майбутньому.")

        next_date = self.calculator.calculate_next_date(last_watered_date, base_interval_days)
        status = self.calculator.determine_status(next_date, current)
        plant = Plant(
            id=None,
            name=clean_name,
            species_id=species_id,
            base_interval_days=base_interval_days,
            last_watered_date=last_watered_date,
            next_watering_date=next_date,
            status=status,
        )
        return self.storage.save_plant(plant)

    def mark_watered(self, plant_id: int, today: Optional[date] = None) -> Plant:
        """Фіксація поливу в один клік («Полито») із записом до історії."""
        current = today or date.today()
        plants = {p.id: p for p in self.storage.load_plants()}
        if plant_id not in plants:
            raise KeyError(f"Рослину з id={plant_id} не знайдено.")

        plant = plants[plant_id]
        active_rule = self.calculator.get_active_rule(current)
        next_date = self.calculator.calculate_next_date(current, plant.base_interval_days, active_rule)
        new_status = self.calculator.determine_status(next_date, current)
        plant.update_watering(current, next_date, new_status)
        self.storage.save_plant(plant)

        event = WateringEvent(
            event_id=None,
            plant_id=plant_id,
            watered_timestamp=datetime.now(),
            applied_k_season=active_rule.k_season_multiplier,
            calculated_next_date=next_date,
        )
        self.storage.append_event(event)
        return plant

    def search_catalog(self, query: str = "", light_level: str = "Усі") -> List[Species]:
        by_name = self.catalog.find_by_name(query)
        if not light_level or light_level == "Усі":
            return by_name
        return [s for s in by_name if s.light_level == light_level]

    def export_schedule_csv(self, file_path: str, today: Optional[date] = None) -> str:
        queue = self.load_today_queue(today)
        with open(file_path, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.writer(f, delimiter=";")
            writer.writerow(["ID", "Назва рослини", "Статус", "Базовий інтервал (дн.)", "Останній полив", "Наступний полив"])
            for p in queue:
                writer.writerow([
                    p.id,
                    p.name,
                    p.status.value,
                    p.base_interval_days,
                    p.last_watered_date.isoformat(),
                    p.next_watering_date.isoformat(),
                ])
        return file_path
