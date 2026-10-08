"""
newspaper.py - გაზეთის ეკრანი (გრაფიკული ინტერფეისი, tkinter).

ეს ფაილი მხოლოდ გამოსახავს თამაშს: ლოგიკა (სტატიის არჩევა, შიფრვა,
ვარაუდის შემოწმება, ვალიდაცია, შედეგების შენახვა) რჩება game.py-სა და
storage.py-ში და აქ უბრალოდ გამოიძახება.

ეკრანზე ჩანს:
    - გაზეთის სათაური და სტატია;
    - შიფრირებული შეტყობინება;
    - ველი საკვანძო სიტყვის ვარაუდისთვის და მცდელობების მრიცხველი.

რაუნდის დასრულებისას (სწორი ვარაუდი ან მცდელობების ამოწურვა) შედეგი
ინახება storage.save_result-ით. შენახვის შეცდომა ეკრანზე ჩანს, მაგრამ
თამაშს არ აჩერებს.

სწორი ვარაუდისას გამოიძახება on_solved(article, word) - ეს იქნება
შემდეგი ეკრანის (ენიგმას მანქანის) გასაღები.
"""

import tkinter as tk

from enigma.components import EnigmaError
from enigma.game import MAX_ATTEMPTS, check_guess, encrypt_message, pick_article
from enigma.storage import save_result

# ფერები: ძველი ქაღალდი და მელანი
PAPER_COLOR = "#eadfc3"
INK_COLOR = "#2b2118"
RULE_COLOR = "#8a7a5c"
GOOD_COLOR = "#2f6b2f"
BAD_COLOR = "#8b2a1e"

# Sylfaen: Windows-ის სერიფიანი შრიფტი, რომელიც ქართულსაც და ლათინურსაც შეიცავს
FONT_FAMILY = "Sylfaen"
CODE_FONT = ("Courier New", 13, "bold")

# ტექსტის გადატანის სიგანე პიქსელებში
WRAP_WIDTH = 740


class NewspaperScreen(tk.Frame):
    """გაზეთის ეკრანი: აჩვენებს სტატიას და იღებს მოთამაშის ვარაუდს."""

    def __init__(self, parent, articles, on_solved=None):
        super().__init__(parent, bg=PAPER_COLOR)
        self._articles = articles      # ვალიდირებული სტატიების სია (game.load_articles)
        self._on_solved = on_solved    # ფუნქცია, რომელიც სწორი ვარაუდისას გამოიძახება
        self._article = None           # მიმდინარე რაუნდის სტატია
        self._attempts_left = MAX_ATTEMPTS
        self._round_over = False

        self._guess_var = tk.StringVar()
        self._build_widgets()
        self.start_round()

    # --- ელემენტების აგება ---
    def _build_widgets(self):
        """ქმნის და ალაგებს ეკრანის ყველა ელემენტს (ერთხელ, ეკრანის შექმნისას)."""
        tk.Label(
            self, text="THE ENIGMA GAZETTE", bg=PAPER_COLOR, fg=INK_COLOR,
            font=(FONT_FAMILY, 28, "bold"),
        ).pack(pady=(14, 2))
        tk.Frame(self, bg=RULE_COLOR, height=3).pack(fill="x", padx=24)

        self._title_label = tk.Label(
            self, bg=PAPER_COLOR, fg=INK_COLOR, font=(FONT_FAMILY, 18, "bold"),
            wraplength=WRAP_WIDTH, justify="center",
        )
        self._title_label.pack(pady=(12, 6))

        # სტატიის ტექსტი: მხოლოდ წასაკითხი, ხოლო მონიშვნა და კოპირება შესაძლებელია
        text_frame = tk.Frame(self, bg=PAPER_COLOR)
        text_frame.pack(fill="both", expand=True, padx=24)
        scrollbar = tk.Scrollbar(text_frame)
        scrollbar.pack(side="right", fill="y")
        self._article_text = tk.Text(
            text_frame, height=6, wrap="word", bg=PAPER_COLOR, fg=INK_COLOR,
            font=(FONT_FAMILY, 13), relief="flat", padx=8, pady=6,
            yscrollcommand=scrollbar.set, state="disabled",
        )
        self._article_text.pack(side="left", fill="both", expand=True)
        scrollbar.config(command=self._article_text.yview)

        tk.Frame(self, bg=RULE_COLOR, height=1).pack(fill="x", padx=24, pady=(8, 6))

        tk.Label(
            self, text="შიფრირებული შეტყობინება:", bg=PAPER_COLOR, fg=INK_COLOR,
            font=(FONT_FAMILY, 12),
        ).pack()
        self._cipher_label = tk.Label(
            self, bg=PAPER_COLOR, fg=INK_COLOR, font=CODE_FONT, wraplength=WRAP_WIDTH,
        )
        self._cipher_label.pack(pady=(2, 8))

        tk.Label(
            self, text="იპოვე სტატიაში საკვანძო სიტყვა (პირველი 3 ასო გახდება როტორების პოზიცია):",
            bg=PAPER_COLOR, fg=INK_COLOR, font=(FONT_FAMILY, 12), wraplength=WRAP_WIDTH,
        ).pack()

        guess_row = tk.Frame(self, bg=PAPER_COLOR)
        guess_row.pack(pady=8)
        self._guess_entry = tk.Entry(
            guess_row, textvariable=self._guess_var, width=22, font=(FONT_FAMILY, 14),
            justify="center",
        )
        self._guess_entry.pack(side="left", padx=(0, 8))
        self._guess_entry.bind("<Return>", self._on_submit)  # Enter ღილაკიც ამოწმებს
        self._submit_button = tk.Button(
            guess_row, text="შემოწმება", font=(FONT_FAMILY, 12), command=self._on_submit,
        )
        self._submit_button.pack(side="left")

        self._attempts_label = tk.Label(
            self, bg=PAPER_COLOR, fg=INK_COLOR, font=(FONT_FAMILY, 11),
        )
        self._attempts_label.pack()

        self._message_label = tk.Label(
            self, bg=PAPER_COLOR, fg=INK_COLOR, font=(FONT_FAMILY, 12, "bold"),
            wraplength=WRAP_WIDTH, justify="center",
        )
        self._message_label.pack(pady=6)

        # შენახვის შეცდომის წარწერა: ცალკეა, რომ ძირითად შეტყობინებას არ გადაეწეროს
        self._save_label = tk.Label(
            self, bg=PAPER_COLOR, fg=BAD_COLOR, font=(FONT_FAMILY, 10),
            wraplength=WRAP_WIDTH, justify="center",
        )
        self._save_label.pack()

        buttons_row = tk.Frame(self, bg=PAPER_COLOR)
        buttons_row.pack(pady=(2, 14))
        tk.Button(
            buttons_row, text="ახალი სტატია", font=(FONT_FAMILY, 11), command=self.start_round,
        ).pack(side="left", padx=6)
        # "გაგრძელება" ჩანს მხოლოდ სწორი ვარაუდის შემდეგ
        self._continue_button = tk.Button(
            buttons_row, text="გაგრძელება ➜", font=(FONT_FAMILY, 11, "bold"),
            command=self._on_continue,
        )

    # --- რაუნდის მართვა ---
    def start_round(self):
        """იწყებს ახალ რაუნდს: ირჩევს სტატიას და აბრუნებს ეკრანს საწყის მდგომარეობაში."""
        self._article = pick_article(self._articles)
        self._attempts_left = MAX_ATTEMPTS
        self._round_over = False

        self._title_label.config(text=self._article["title"])
        self._set_article_text(self._article["text"])
        self._cipher_label.config(text=encrypt_message(self._article))

        self._guess_var.set("")
        self._guess_entry.config(state="normal")
        self._submit_button.config(state="normal")
        self._continue_button.pack_forget()
        self._show_message("", INK_COLOR)
        self._save_label.config(text="")  # წინა რაუნდის შენახვის შეცდომას ვასუფთავებთ
        self._update_attempts()
        self._guess_entry.focus_set()

    def _set_article_text(self, text):
        """ათავსებს სტატიის ტექსტს Text ელემენტში (ჯერ ვხსნით, მერე ისევ ვკეტავთ)."""
        self._article_text.config(state="normal")
        self._article_text.delete("1.0", "end")
        self._article_text.insert("1.0", text)
        self._article_text.config(state="disabled")

    def _update_attempts(self):
        """განაახლებს დარჩენილი მცდელობების წარწერას."""
        self._attempts_label.config(text=f"დარჩენილია მცდელობა: {self._attempts_left}")

    def _show_message(self, text, color):
        """აჩვენებს შეტყობინებას მოცემული ფერით."""
        self._message_label.config(text=text, fg=color)

    def _finish_round(self):
        """რაუნდის დასრულებისას კეტავს შეყვანის ველს და ღილაკს."""
        self._round_over = True
        self._guess_entry.config(state="disabled")
        self._submit_button.config(state="disabled")

    def _save_round(self, guess, success):
        """ინახავს რაუნდის შედეგს storage.save_result-ით.

        შეცდომისას (EnigmaError) აჩვენებს მას ეკრანზე და თამაშს არ აჩერებს.
        """
        try:
            save_result(
                self._article["title"], guess.strip(), success, self._attempts_left,
            )
        except EnigmaError as error:
            self._save_label.config(text=f"შედეგი ვერ შეინახა: {error}")

    # --- მოთამაშის მოქმედებები ---
    def _on_submit(self, event=None):
        """ამოწმებს ვარაუდს game.check_guess-ით. არასწორი ფორმატი მცდელობას არ ხარჯავს."""
        if self._round_over:
            return

        guess = self._guess_var.get()
        try:
            decrypted, success = check_guess(self._article, guess)
        except EnigmaError as error:
            self._show_message(f"შეცდომა: {error}", BAD_COLOR)
            return

        if success:
            self._show_message(f"სწორია! მანქანამ გაშიფრა: {decrypted}", GOOD_COLOR)
            self._finish_round()
            self._save_round(guess, True)  # წარმატებული რაუნდის შენახვა
            if self._on_solved is not None:
                self._continue_button.pack(side="left", padx=6)
            return

        self._attempts_left -= 1
        self._update_attempts()
        if self._attempts_left == 0:
            self._show_message(
                f"მცდელობები ამოიწურა. საკვანძო სიტყვა იყო: {self._article['secret_word']}",
                BAD_COLOR,
            )
            self._finish_round()
            self._save_round(guess, False)  # წაგებული რაუნდის შენახვა
        else:
            self._show_message(
                f"მანქანამ გაშიფრა: {decrypted} - უაზრობაა, სცადე თავიდან", BAD_COLOR,
            )

    def _on_continue(self):
        """გადასცემს გამოცნობილ სიტყვას გარე ფუნქციას (შემდეგი ეკრანისთვის)."""
        if self._on_solved is not None:
            self._on_solved(self._article, self._article["secret_word"])