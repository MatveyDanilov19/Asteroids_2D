"""Модуль графического интерфейса для ввода параметров игры."""

import tkinter as tk
from tkinter import messagebox


def get_simulation_params() -> dict | None:
    """Открывает окно настроек и возвращает словарь параметров игры."""
    result = {}

    root = tk.Tk()
    root.title("Настройки симуляции")
    root.geometry("380x370")
    root.resizable(False, False)

    fields = [
        ("Количество шаров:", "35"),
        ("Ширина области (px):", "1000"),
        ("Высота области (px):", "700"),
        ("Мин. радиус шара (px):", "10"),
        ("Макс. радиус шара (px):", "28"),
        ("Мин. скорость (px/с):", "50"),
        ("Макс. скорость (px/с):", "180"),
    ]

    entries = {}
    for idx, (label_text, default_val) in enumerate(fields):
        tk.Label(root, text=label_text, anchor="w", font=("Arial", 10)).grid(
            row=idx, column=0, padx=15, pady=7, sticky="w"
        )
        entry = tk.Entry(root, width=15, font=("Arial", 10))
        entry.insert(0, default_val)
        entry.grid(row=idx, column=1, padx=15, pady=7)
        entries[label_text] = entry

    def on_start():
        try:
            params = {
                "count": int(entries["Количество шаров:"].get()),
                "width": int(entries["Ширина области (px):"].get()),
                "height": int(entries["Высота области (px):"].get()),
                "min_r": float(entries["Мин. радиус шара (px):"].get()),
                "max_r": float(entries["Макс. радиус шара (px):"].get()),
                "min_v": float(entries["Мин. скорость (px/с):"].get()),
                "max_v": float(entries["Макс. скорость (px/с):"].get()),
            }

            if (
                params["count"] <= 0
                or params["width"] < 200
                or params["height"] < 200
            ):
                raise ValueError(
                    "Проверьте корректность размеров области и числа шаров."
                )
            if params["min_r"] <= 0 or params["min_r"] > params["max_r"]:
                raise ValueError(
                    "Мин. радиус должен быть больше 0 и не больше макс."
                )
            if params["min_v"] < 0 or params["min_v"] > params["max_v"]:
                raise ValueError(
                    "Мин. скорость не может быть меньше 0 или больше макс."
                )

            result.update(params)
            root.destroy()

        except ValueError as err:
            messagebox.showerror("Ошибка ввода", str(err))

    btn = tk.Button(
        root,
        text="Запустить игру",
        command=on_start,
        bg="#2e7d32",
        fg="white",
        font=("Arial", 10, "bold"),
        cursor="hand2",
    )
    btn.grid(
        row=len(fields), column=0, columnspan=2, pady=15, ipadx=20, ipady=6
    )

    hint = tk.Label(
        root,
        text=(
            "Управление в игре:\n"
            "[W/A/D] — полёт  |  [Пробел] — огонь  |  [T] — сетка"
        ),
        fg="#555555",
        font=("Arial", 8),
    )
    hint.grid(row=len(fields) + 1, column=0, columnspan=2, pady=5)

    root.mainloop()
    return result if result else None
