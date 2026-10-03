"""
main.py - პროგრამის შესასვლელი წერტილი.

ქმნის მთავარ ფანჯარას, ტვირთავს სტატიებს და აჩვენებს ეკრანებს:
    1. გაზეთის ეკრანი (სიტყვის გამოცნობა);
    2. ენიგმას მანქანის ეკრანი (სწორი სიტყვის შემდეგ).
გაშვება პროექტის ძირითადი ფოლდერიდან:  python main.py
"""

import tkinter as tk
from tkinter import messagebox

from enigma.components import EnigmaError
from enigma.game import load_articles
from enigma.machine_view import MachineScreen
from enigma.newspaper import NewspaperScreen


def clear_window(window):
    """შლის ფანჯარაში არსებულ ეკრანს, რომ მის ადგილას ახალი გამოჩნდეს."""
    for child in window.winfo_children():
        child.destroy()


def show_newspaper(window, articles):
    """აჩვენებს გაზეთის ეკრანს. სწორი ვარაუდისას გადადის მანქანის ეკრანზე."""
    clear_window(window)
    screen = NewspaperScreen(
        window, articles,
        on_solved=lambda article, word: show_machine(window, articles, article, word),
    )
    screen.pack(fill="both", expand=True)


def show_machine(window, articles, article, word):
    """აჩვენებს ენიგმას მანქანის ეკრანს გამოცნობილი სიტყვით; 'უკან' აბრუნებს გაზეთზე."""
    clear_window(window)
    screen = MachineScreen(
        window, article, word,
        on_back=lambda: show_newspaper(window, articles),
    )
    screen.pack(fill="both", expand=True)


def main():
    """ქმნის ფანჯარას და უშვებს პროგრამას."""
    window = tk.Tk()
    window.title("Enigma")
    window.geometry("920x740")
    window.minsize(880, 700)

    # სტატიების ჩატვირთვა: თუ ფაილი დაზიანებულია, მომხმარებელი შეცდომას ნახავს და პროგრამა დაიხურება
    try:
        articles = load_articles()
    except EnigmaError as error:
        messagebox.showerror("ჩატვირთვის შეცდომა", str(error))
        window.destroy()
        return

    show_newspaper(window, articles)
    window.mainloop()


if __name__ == "__main__":
    main()
