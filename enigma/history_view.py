"""
history_view.py - "ისტორიის" ფანჯარა (გრაფიკული ინტერფეისი, tkinter).

ფანჯარა აჩვენებს შენახულ შედეგებს (ახალი ზემოთაა) და საშუალებას იძლევა:
    - წაიშალოს ერთი არჩეული ჩანაწერი;
    - გასუფთავდეს მთელი ისტორია.

ლოგიკა აქ არ არის: წაკითხვა, წაშლა და ტექსტად გარდაქმნა storage.py-ს
ფუნქციებს (load_results, delete_result, clear_results, format_result)
ეკისრება. შეცდომა (EnigmaError) ფანჯარაში წარწერად ჩანს და ფანჯარას
არ ხურავს.
"""

import tkinter as tk
from tkinter import messagebox

from enigma.components import EnigmaError
from enigma.storage import clear_results, delete_result, format_result, load_results

# ფერები და შრიფტი იგივეა, რაც გაზეთის ეკრანზე
PAPER_COLOR = "#eadfc3"
INK_COLOR = "#2b2118"
GOOD_COLOR = "#2f6b2f"
BAD_COLOR = "#8b2a1e"
FONT_FAMILY = "Sylfaen"


class HistoryWindow(tk.Toplevel):
    """ცალკე ფანჯარა შენახული შედეგების სიით, წაშლისა და გასუფთავების ღილაკებით."""

    def __init__(self, parent):
        super().__init__(parent, bg=PAPER_COLOR)
        self.title("ისტორია")
        self.geometry("900x420")
        self.transient(parent)   # ფანჯარა მთავარ ფანჯარაზე მაღლა რჩება
        self.grab_set()          # სანამ ღიაა, მთავარ ფანჯარასთან მუშაობა დროებით შეჩერებულია

        self._results = []       # ფაილიდან წაკითხული ჩანაწერები (ფაილის თანმიმდევრობით)
        self._build_widgets()
        self.refresh()

    # --- ელემენტების აგება ---
    def _build_widgets(self):
        """ქმნის და ალაგებს ფანჯრის ელემენტებს (ერთხელ, ფანჯრის შექმნისას)."""
        tk.Label(
            self, text="თამაშების ისტორია", bg=PAPER_COLOR, fg=INK_COLOR,
            font=(FONT_FAMILY, 18, "bold"),
        ).pack(pady=(12, 6))

        list_frame = tk.Frame(self, bg=PAPER_COLOR)
        list_frame.pack(fill="both", expand=True, padx=16)

        y_scroll = tk.Scrollbar(list_frame, orient="vertical")
        y_scroll.pack(side="right", fill="y")
        x_scroll = tk.Scrollbar(list_frame, orient="horizontal")
        x_scroll.pack(side="bottom", fill="x")

        self._listbox = tk.Listbox(
            list_frame, font=(FONT_FAMILY, 11), bg=PAPER_COLOR, fg=INK_COLOR,
            selectmode="single", activestyle="none",
            yscrollcommand=y_scroll.set, xscrollcommand=x_scroll.set,
        )
        self._listbox.pack(side="left", fill="both", expand=True)
        y_scroll.config(command=self._listbox.yview)
        x_scroll.config(command=self._listbox.xview)

        # შეტყობინებების წარწერა (შეცდომა ან მოქმედების შედეგი)
        self._status_label = tk.Label(
            self, bg=PAPER_COLOR, fg=INK_COLOR, font=(FONT_FAMILY, 11),
            wraplength=860, justify="center",
        )
        self._status_label.pack(pady=6)

        buttons_row = tk.Frame(self, bg=PAPER_COLOR)
        buttons_row.pack(pady=(0, 12))
        tk.Button(
            buttons_row, text="არჩეულის წაშლა", font=(FONT_FAMILY, 11),
            command=self._on_delete,
        ).pack(side="left", padx=6)
        tk.Button(
            buttons_row, text="ყველას გასუფთავება", font=(FONT_FAMILY, 11),
            command=self._on_clear,
        ).pack(side="left", padx=6)
        tk.Button(
            buttons_row, text="დახურვა", font=(FONT_FAMILY, 11), command=self.destroy,
        ).pack(side="left", padx=6)

    # --- სიის განახლება ---
    def refresh(self, message="", color=INK_COLOR):
        """თავიდან კითხულობს ფაილს და ავსებს სიას (ახალი ჩანაწერი ზემოთაა)."""
        self._listbox.delete(0, "end")
        try:
            self._results = load_results()
        except EnigmaError as error:
            self._results = []
            self._show_status(f"შეცდომა: {error}", BAD_COLOR)
            return

        for result in reversed(self._results):
            try:
                self._listbox.insert("end", format_result(result))
            except (KeyError, TypeError):
                self._listbox.insert("end", "(დაზიანებული ჩანაწერი)")

        if message:
            self._show_status(message, color)
        elif not self._results:
            self._show_status("ისტორია ცარიელია", INK_COLOR)
        else:
            self._show_status(f"სულ ჩანაწერი: {len(self._results)}", INK_COLOR)

    def _show_status(self, text, color):
        """აჩვენებს შეტყობინებას მოცემული ფერით."""
        self._status_label.config(text=text, fg=color)

    # --- მოთამაშის მოქმედებები ---
    def _on_delete(self):
        """შლის არჩეულ ჩანაწერს storage.delete_result-ით."""
        selection = self._listbox.curselection()
        if not selection:
            self._show_status("ჯერ აირჩიე ჩანაწერი სიაში", BAD_COLOR)
            return

        # სია ეკრანზე შებრუნებულია (ახალი ზემოთ), ფაილში კი პირიქით;
        # ამიტომ ეკრანის ნომერს ფაილის ნომრად ვაქცევთ
        file_index = len(self._results) - 1 - selection[0]
        if not messagebox.askyesno("დადასტურება", "წავშალო არჩეული ჩანაწერი?", parent=self):
            return

        try:
            delete_result(file_index)
        except EnigmaError as error:
            self._show_status(f"შეცდომა: {error}", BAD_COLOR)
            return
        self.refresh("ჩანაწერი წაიშალა", GOOD_COLOR)

    def _on_clear(self):
        """შლის მთელ ისტორიას storage.clear_results-ით."""
        if not self._results:
            self._show_status("ისტორია უკვე ცარიელია", INK_COLOR)
            return
        if not messagebox.askyesno("დადასტურება", "წავშალო მთელი ისტორია?", parent=self):
            return

        try:
            clear_results()
        except EnigmaError as error:
            self._show_status(f"შეცდომა: {error}", BAD_COLOR)
            return
        self.refresh("ისტორია გასუფთავდა", GOOD_COLOR)
