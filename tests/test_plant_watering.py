"""Модульні тести ПЗ PlantWatering (перевірка сезонів, високосного року, БД і черги)."""

import os
import tempfile
import unittest
from datetime import date

from src.calculator import WateringCalculator
from src.catalog import PlantCatalog
from src.dispatcher import TaskDispatcher
from src.models import WateringStatus
from src.storage import LocalStorage


class TestWateringCalculator(unittest.TestCase):
    def setUp(self) -> None:
        self.calc = WateringCalculator()

    def test_summer_and_winter_coefficients(self) -> None:
        # Літо: K_season = 1.0 -> 4 * 1.0 = 4 дні
        self.assertEqual(self.calc.calculate_next_date(date(2026, 7, 10), 4), date(2026, 7, 14))
        # Зима: K_season = 1.5 -> ceil(5 * 1.5) = 8 днів
        self.assertEqual(self.calc.calculate_next_date(date(2026, 1, 10), 5), date(2026, 1, 18))

    def test_leap_year_and_year_transition(self) -> None:
        # Високосний рік (2024): 26 лютого + ceil(4 * 1.5)=6 днів -> 3 березня
        self.assertEqual(self.calc.calculate_next_date(date(2024, 2, 26), 4), date(2024, 3, 3))
        # Перехід року: 29 грудня + ceil(4 * 1.5)=6 днів -> 4 січня наступного року
        self.assertEqual(self.calc.calculate_next_date(date(2026, 12, 29), 4), date(2027, 1, 4))

    def test_invalid_interval_raises(self) -> None:
        with self.assertRaises(ValueError):
            self.calc.calculate_next_date(date(2026, 5, 1), 0)
        with self.assertRaises(ValueError):
            self.calc.calculate_next_date(date(2026, 5, 1), 65)

    def test_determine_status(self) -> None:
        today = date(2026, 11, 23)
        self.assertEqual(self.calc.determine_status(date(2026, 11, 20), today), WateringStatus.OVERDUE)
        self.assertEqual(self.calc.determine_status(date(2026, 11, 23), today), WateringStatus.TODAY)
        self.assertEqual(self.calc.determine_status(date(2026, 11, 26), today), WateringStatus.PLANNED)


class TestDispatcherAndStorage(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self.tmp.close()
        self.storage = LocalStorage(self.tmp.name)
        self.dispatcher = TaskDispatcher(storage=self.storage, catalog=PlantCatalog())

    def tearDown(self) -> None:
        import gc
        self.storage = None
        self.dispatcher = None
        gc.collect()
        if os.path.exists(self.tmp.name):
            try:
                os.remove(self.tmp.name)
            except PermissionError:
                pass

    def test_catalog_search_and_filter(self) -> None:
        res = self.dispatcher.search_catalog(query="фікус")
        self.assertEqual(len(res), 2)
        shade = self.dispatcher.search_catalog(light_level="Тіньовитривала")
        self.assertGreaterEqual(len(shade), 4)

    def test_add_mark_watered_and_history(self) -> None:
        today = date(2026, 11, 23)
        plant = self.dispatcher.add_plant("Монстера делікатесна", 7, date(2026, 11, 10), today=today)
        self.assertEqual(plant.status, WateringStatus.OVERDUE)

        updated = self.dispatcher.mark_watered(plant.id, today=today)
        self.assertEqual(updated.last_watered_date, today)
        self.assertEqual(updated.status, WateringStatus.PLANNED)

        history = self.storage.load_history(plant.id)
        self.assertEqual(len(history), 1)


if __name__ == "__main__":
    unittest.main()
