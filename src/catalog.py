"""Локальний довідник PlantCatalog на 25 популярних кімнатних рослин."""

from typing import List, Optional
from src.models import Species

DEFAULT_SPECIES: List[Species] = [
    Species(1, "Монстера делікатесна", "Помірне світло", 7, True),
    Species(2, "Фікус Бенджаміна", "Яскраве розсіяне", 5, True),
    Species(3, "Заміокулькас", "Тіньовитривала", 14, False),
    Species(4, "Сансевієрія (Тещин язик)", "Тіньовитривала", 14, False),
    Species(5, "Спатифілум", "Помірне світло", 4, True),
    Species(6, "Хлорофітум", "Помірне світло", 5, True),
    Species(7, "Алое вера", "Яскраве пряме", 12, False),
    Species(8, "Орхідея Фаленопсис", "Яскраве розсіяне", 8, True),
    Species(9, "Драцена облямована", "Помірне світло", 7, True),
    Species(10, "Антуріум Андре", "Яскраве розсіяне", 5, True),
    Species(11, "Красула (Грошове дерево)", "Яскраве пряме", 10, False),
    Species(12, "Фіалка узамбарська", "Яскраве розсіяне", 4, False),
    Species(13, "Калатея", "Тіньовитривала", 4, True),
    Species(14, "Папороть Нефролепіс", "Тіньовитривала", 3, True),
    Species(15, "Пеларгонія (Герань)", "Яскраве пряме", 5, False),
    Species(16, "Шефлера", "Яскраве розсіяне", 6, True),
    Species(17, "Юка слонова", "Яскраве пряме", 10, False),
    Species(18, "Дифенбахія", "Помірне світло", 5, True),
    Species(19, "Бегонія декоративна", "Яскраве розсіяне", 4, True),
    Species(20, "Епіпремнум золотистий", "Помірне світло", 6, True),
    Species(21, "Кактус Ехінопсис", "Яскраве пряме", 18, False),
    Species(22, "Пеперомія", "Помірне світло", 7, False),
    Species(23, "Цикламен перський", "Яскраве розсіяне", 4, False),
    Species(24, "Кротон (Кодіеум)", "Яскраве розсіяне", 4, True),
    Species(25, "Фікус Еластика", "Яскраве розсіяне", 7, True),
]


class PlantCatalog:
    """Забезпечує локальний пошук за підрядком назви та фільтрацію за освітленням."""

    def __init__(self, species_list: Optional[List[Species]] = None) -> None:
        self.species_list = species_list or list(DEFAULT_SPECIES)

    def find_by_name(self, substring: str) -> List[Species]:
        query = substring.strip().lower()
        if not query:
            return list(self.species_list)
        return [s for s in self.species_list if query in s.title.lower()]

    def filter_by_light(self, light_level: str) -> List[Species]:
        if not light_level or light_level == "Усі":
            return list(self.species_list)
        return [s for s in self.species_list if s.light_level == light_level]

    def get_by_id(self, species_id: int) -> Optional[Species]:
        for s in self.species_list:
            if s.species_id == species_id:
                return s
        return None
