"""Графічний інтерфейс користувача PlantWatering на базі tkinter (українська локалізація)."""

from datetime import date
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from src.dispatcher import TaskDispatcher
from src.models import WateringStatus


class PlantWateringApp(tk.Tk):
    """Головне вікно застосунку PlantWatering."""

    def __init__(self, dispatcher: TaskDispatcher | None = None) -> None:
        super().__init__()
        self.dispatcher = dispatcher or TaskDispatcher()
        self.title("PlantWatering — Планувальник поливу рослин")
        self.geometry("860x560")
        self.minsize(780, 500)

        self._build_ui()
        self._refresh_all()

    def _build_ui(self) -> None:
        notebook = ttk.Notebook(self)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.tab_today = ttk.Frame(notebook)
        self.tab_catalog = ttk.Frame(notebook)
        self.tab_history = ttk.Frame(notebook)

        notebook.add(self.tab_today, text="Сьогодні")
        notebook.add(self.tab_catalog, text="Каталог рослин")
        notebook.add(self.tab_history, text="Історія поливів")

        self._build_today_tab()
        self._build_catalog_tab()
        self._build_history_tab()

    def _build_today_tab(self) -> None:
        top = ttk.Frame(self.tab_today)
        top.pack(fill=tk.X, padx=8, pady=8)

        rule = self.dispatcher.calculator.get_active_rule(date.today())
        ttk.Label(
            top,
            text=f"Поточний сезон: {rule.season_name} (K_season = {rule.k_season_multiplier:.2f})",
            font=("TkDefaultFont", 10, "bold"),
        ).pack(side=tk.LEFT)

        ttk.Button(top, text="Експорт графіка (CSV)", command=self._export_csv).pack(side=tk.RIGHT, padx=4)
        ttk.Button(top, text="Видалити обрану", command=self._delete_selected).pack(side=tk.RIGHT, padx=4)
        ttk.Button(top, text="Полито (1 клік)", command=self._mark_selected_watered).pack(side=tk.RIGHT, padx=4)

        cols = ("id", "name", "status", "interval", "last", "next")
        self.today_tree = ttk.Treeview(self.tab_today, columns=cols, show="headings", height=16)
        headers = {
            "id": ("ID", 45),
            "name": ("Назва рослини", 240),
            "status": ("Статус", 120),
            "interval": ("Інтервал (дн.)", 105),
            "last": ("Останній полив", 130),
            "next": ("Наступний полив", 130),
        }
        for c, (title, width) in headers.items():
            self.today_tree.heading(c, text=title)
            self.today_tree.column(c, width=width, anchor=tk.CENTER if c != "name" else tk.W)
        self.today_tree.pack(fill=tk.BOTH, expand=True, padx=8, pady=(0, 8))

    def _build_catalog_tab(self) -> None:
        search_bar = ttk.Frame(self.tab_catalog)
        search_bar.pack(fill=tk.X, padx=8, pady=8)

        ttk.Label(search_bar, text="Пошук:").pack(side=tk.LEFT)
        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", lambda *_: self._refresh_catalog())
        ttk.Entry(search_bar, textvariable=self.search_var, width=26).pack(side=tk.LEFT, padx=6)

        ttk.Label(search_bar, text="Освітлення:").pack(side=tk.LEFT, padx=(10, 4))
        self.light_var = tk.StringVar(value="Усі")
        light_cb = ttk.Combobox(
            search_bar,
            textvariable=self.light_var,
            state="readonly",
            width=18,
            values=["Усі", "Яскраве пряме", "Яскраве розсіяне", "Помірне світло", "Тіньовитривала"],
        )
        light_cb.pack(side=tk.LEFT)
        light_cb.bind("<<ComboboxSelected>>", lambda *_: self._refresh_catalog())

        ttk.Label(search_bar, text="Останній полив (РРРР-ММ-ДД):").pack(side=tk.LEFT, padx=(10, 4))
        self.last_date_var = tk.StringVar(value=date.today().isoformat())
        ttk.Entry(search_bar, textvariable=self.last_date_var, width=12).pack(side=tk.LEFT)

        ttk.Button(search_bar, text="Додати рослину", command=self._add_from_catalog).pack(side=tk.RIGHT)

        cols = ("id", "title", "light", "interval", "misting")
        self.catalog_tree = ttk.Treeview(self.tab_catalog, columns=cols, show="headings", height=16)
        for c, title, w in [
            ("id", "ID", 45),
            ("title", "Вид рослини", 250),
            ("light", "Освітлення", 160),
            ("interval", "Базовий інтервал (дн.)", 150),
            ("misting", "Обприскування", 120),
        ]:
            self.catalog_tree.heading(c, text=title)
            self.catalog_tree.column(c, width=w, anchor=tk.CENTER if c != "title" else tk.W)
        self.catalog_tree.pack(fill=tk.BOTH, expand=True, padx=8, pady=(0, 8))

    def _build_history_tab(self) -> None:
        self.history_list = tk.Listbox(self.tab_history, font=("TkDefaultFont", 10))
        self.history_list.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)

    def _refresh_all(self) -> None:
        self._refresh_today()
        self._refresh_catalog()
        self._refresh_history()

    def _refresh_today(self) -> None:
        self.today_tree.delete(*self.today_tree.get_children())
        for p in self.dispatcher.load_today_queue():
            self.today_tree.insert(
                "",
                tk.END,
                values=(
                    p.id,
                    p.name,
                    p.status.value,
                    p.base_interval_days,
                    p.last_watered_date.isoformat(),
                    p.next_watering_date.isoformat(),
                ),
            )

    def _refresh_catalog(self) -> None:
        self.catalog_tree.delete(*self.catalog_tree.get_children())
        for sp in self.dispatcher.search_catalog(self.search_var.get(), self.light_var.get()):
            self.catalog_tree.insert(
                "",
                tk.END,
                values=(sp.species_id, sp.title, sp.light_level, sp.default_interval_days, "Так" if sp.misting_sensitive else "Ні"),
            )

    def _refresh_history(self) -> None:
        self.history_list.delete(0, tk.END)
        for ev in self.dispatcher.storage.load_history():
            self.history_list.insert(tk.END, ev.format_log_entry())

    def _mark_selected_watered(self) -> None:
        sel = self.today_tree.selection()
        if not sel:
            messagebox.showinfo("Увага", "Оберіть рослину зі списку «Сьогодні».")
            return
        plant_id = int(self.today_tree.item(sel[0], "values")[0])
        self.dispatcher.mark_watered(plant_id)
        self._refresh_all()

    def _delete_selected(self) -> None:
        sel = self.today_tree.selection()
        if not sel:
            return
        plant_id = int(self.today_tree.item(sel[0], "values")[0])
        self.dispatcher.storage.delete_plant(plant_id)
        self._refresh_all()

    def _add_from_catalog(self) -> None:
        sel = self.catalog_tree.selection()
        if not sel:
            messagebox.showinfo("Увага", "Оберіть вид рослини у каталозі.")
            return
        vals = self.catalog_tree.item(sel[0], "values")
        try:
            last_dt = date.fromisoformat(self.last_date_var.get().strip())
            self.dispatcher.add_plant(
                name=str(vals[1]),
                base_interval_days=int(vals[3]),
                last_watered_date=last_dt,
                species_id=int(vals[0]),
            )
            self._refresh_all()
            messagebox.showinfo("Готово", f"Рослину «{vals[1]}» додано до списку «Мої рослини».")
        except ValueError as err:
            messagebox.showerror("Помилка валідації", str(err))

    def _export_csv(self) -> None:
        path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV файл", "*.csv")])
        if path:
            self.dispatcher.export_schedule_csv(path)
            messagebox.showinfo("Експорт", f"Графік успішно збережено у файл: {path}")


if __name__ == "__main__":
    app = PlantWateringApp()
    app.mainloop()
