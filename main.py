"""
main.py - პროგრამის შესასვლელი წერტილი.

ქმნის მთავარ ფანჯარას, ტვირთავს სტატიებს და აჩვენებს გაზეთის ეკრანს.
გაშვება პროექტის ძირითადი ფოლდერიდან:  python main.py
"""

import tkinter as tk
from tkinter import messagebox

from enigma.components import EnigmaError
from enigma.game import key_from_word, load_articles
from enigma.newspaper import NewspaperScreen


def on_solved(article, word):
    """გამოიძახება, როცა მოთამაშემ სწორად გამოიცნო სიტყვა.
    ჯერჯერობით მხოლოდ აჩვენებს გასაღებს; შემდეგ ნაბიჯში აქ გაიხსნება ენიგმას ეკრანი."""
    positions = key_from_word(word)
    messagebox.showinfo(
        "მზადაა",
        f"სიტყვა: {word}\nროტორების საწყისი პოზიცია: {positions}\n\n"
        "ენიგმას მანქანის ეკრანს შემდეგ ნაბიჯში დავამატებთ.",
    )


def main():
    """ქმნის ფანჯარას და უშვებს პროგრამას."""
    window = tk.Tk()
    window.title("Enigma")
    window.geometry("820x700")
    window.minsize(720, 600)

    # სტატიების ჩატვირთვა: თუ ფაილი დაზიანებულია, მომხმარებელი შეცდომას ნახავს და პროგრამა დაიხურება
    try:
        articles = load_articles()
    except EnigmaError as error:
        messagebox.showerror("ჩატვირთვის შეცდომა", str(error))
        window.destroy()
        return

    screen = NewspaperScreen(window, articles, on_solved=on_solved)
    screen.pack(fill="both", expand=True)
    window.mainloop()


if __name__ == "__main__":
    main()

