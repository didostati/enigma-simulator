"""
machine_view.py - ენიგმას მანქანის ეკრანი (გრაფიკული ინტერფეისი, tkinter).

ეს ფაილი მხოლოდ გამოსახავს მანქანას; შიფრვის ლოგიკა რჩება machine.py-სა და
components.py-ში და აქ უბრალოდ გამოიძახება.

ეკრანზე ჩანს:
    - სამი როტორი მიმდინარე პოზიციებით (საწყისი პოზიცია = გამოცნობილი სიტყვის პირველი 3 ასო);
    - ნათურების დაფა: დაჭერილი ასოს შიფრი ინთება;
    - კლავიატურა (მაუსით ან ნამდვილი კლავიატურით, ინგლისური განლაგებით);
    - შეყვანილი და მიღებული ტექსტი;
    - პლაგბორდი: ასოების წყვილების დამატება და წაშლა.
"""

import tkinter as tk

from enigma.components import ALPHABET, EnigmaError
from enigma.game import DEFAULT_ROTORS, encrypt_message, key_from_word
from enigma.machine import EnigmaMachine

# ფერები: მუქი "მეტალის" კორპუსი
BODY_COLOR = "#25211c"
PANEL_COLOR = "#3a342c"
TEXT_COLOR = "#eadfc3"
LAMP_OFF_BG = "#1a1814"
LAMP_OFF_FG = "#6d6455"
LAMP_ON_BG = "#ffd84a"
LAMP_ON_FG = "#2b2118"
KEY_BG = "#d9cfb4"
KEY_FG = "#2b2118"
GOOD_COLOR = "#8fd18f"
BAD_COLOR = "#ff8a7a"

FONT_FAMILY = "Sylfaen"
CODE_FONT = ("Courier New", 14, "bold")

# კლავიშების განლაგება (ნამდვილი ენიგმას QWERTZ რიგები)
KEY_ROWS = ("QWERTZUIO", "ASDFGHJK", "PYXCVBNML")

# რამდენ მილიწამს ანათებს ნათურა
LAMP_DURATION_MS = 600

# ტექსტის გადატანის სიგანე მარცხენა სვეტში (პიქსელი)
WRAP_WIDTH = 540


def allow_one_char(new_text):
    """Entry-ის ვალიდაცია: ველში მაქსიმუმ ერთი სიმბოლო დაიწერება."""
    return len(new_text) <= 1


class MachineScreen(tk.Frame):
    """ენიგმას მანქანის ეკრანი: როტორები, ნათურები, კლავიატურა და პლაგბორდი."""

    def __init__(self, parent, article, word, on_back=None):
        super().__init__(parent, bg=BODY_COLOR)
        self._article = article
        self._word = word.upper()
        self._on_back = on_back

        # საწყისი პოზიცია გამოცნობილი სიტყვის პირველი 3 ასოა (იგივე წესი, რაც game.py-შია)
        self._start_positions = key_from_word(word)
        self._machine = EnigmaMachine(DEFAULT_ROTORS, self._start_positions)
        self._ciphertext = encrypt_message(article)

        self._input_text = ""    # რაც მოთამაშემ აკრიფა
        self._output_text = ""   # რაც მანქანამ დააბრუნა
        self._lit_letter = None  # ახლა რომელი ნათურა ანათებს
        self._lamp_job = None    # გამორთვის ტაიმერის ნომერი (after)

        self._build_widgets()
        self._refresh()

        # ნამდვილი კლავიატურის მხარდაჭერა: ვუსმენთ მთელ ფანჯარას
        self._key_binding = self.winfo_toplevel().bind("<Key>", self._on_key_event, add="+")

    # --- ელემენტების აგება ---
    def _build_widgets(self):
        """ქმნის ეკრანის ყველა ელემენტს: მარცხნივ მანქანა, მარჯვნივ პლაგბორდი."""
        tk.Label(
            self, text="ENIGMA", bg=BODY_COLOR, fg=TEXT_COLOR, font=(FONT_FAMILY, 24, "bold"),
        ).pack(pady=(10, 0))
        tk.Label(
            self,
            text=f"გასაღები: {self._start_positions}   ·   როტორები: {' - '.join(DEFAULT_ROTORS)}",
            bg=BODY_COLOR, fg=TEXT_COLOR, font=(FONT_FAMILY, 11),
        ).pack()

        content = tk.Frame(self, bg=BODY_COLOR)
        content.pack(fill="both", expand=True, padx=16, pady=8)

        left = tk.Frame(content, bg=BODY_COLOR)
        left.pack(side="left", fill="both", expand=True)
        self._build_plugboard_panel(content)

        self._build_rotors(left)
        tk.Label(
            left, text=f"ამოსაშიფრი შეტყობინება:  {self._ciphertext}", bg=BODY_COLOR,
            fg=TEXT_COLOR, font=("Courier New", 12, "bold"), wraplength=WRAP_WIDTH,
        ).pack(pady=(4, 8))

        self._lamps = self._build_rows(left, self._make_lamp)
        tk.Frame(left, bg=BODY_COLOR, height=8).pack()
        self._keys = self._build_rows(left, self._make_key)
        tk.Button(
            left, text="ინტერვალი", width=24, bg=KEY_BG, fg=KEY_FG, font=(FONT_FAMILY, 10),
            command=self._add_space,
        ).pack(pady=(4, 8))

        self._build_texts(left)
        self._build_bottom_buttons(left)

    def _build_rotors(self, parent):
        """სამი როტორის ფანჯარა: მარცხენა, შუა, მარჯვენა."""
        row = tk.Frame(parent, bg=BODY_COLOR)
        row.pack(pady=(6, 4))
        self._rotor_labels = []
        for name in DEFAULT_ROTORS:
            box = tk.Frame(row, bg=PANEL_COLOR, padx=14, pady=6)
            box.pack(side="left", padx=8)
            letter_label = tk.Label(
                box, text="A", width=2, bg=LAMP_OFF_BG, fg=TEXT_COLOR,
                font=("Courier New", 28, "bold"),
            )
            letter_label.pack()
            tk.Label(
                box, text=f"როტორი {name}", bg=PANEL_COLOR, fg=TEXT_COLOR, font=(FONT_FAMILY, 10),
            ).pack()
            self._rotor_labels.append(letter_label)

    def _build_rows(self, parent, factory):
        """აგებს ასოების რიგებს (QWERTZ). factory ქმნის თითო ელემენტს; აბრუნებს {ასო: ელემენტი}."""
        widgets = {}
        for row_letters in KEY_ROWS:
            row = tk.Frame(parent, bg=BODY_COLOR)
            row.pack(pady=2)
            for letter in row_letters:
                widget = factory(row, letter)
                widget.pack(side="left", padx=3)
                widgets[letter] = widget
        return widgets

    def _make_lamp(self, row, letter):
        """ქმნის ერთ ნათურას (ჩვეულებრივ ჩამქრალია)."""
        return tk.Label(
            row, text=letter, width=3, bg=LAMP_OFF_BG, fg=LAMP_OFF_FG, relief="sunken", bd=2,
            font=CODE_FONT,
        )

    def _make_key(self, row, letter):
        """ქმნის ერთ კლავიშს; დაჭერისას გამოიძახება _press(letter)."""
        return tk.Button(
            row, text=letter, width=3, bg=KEY_BG, fg=KEY_FG, font=CODE_FONT,
            command=lambda: self._press(letter),
        )

    def _build_texts(self, parent):
        """შეყვანილი და მიღებული ტექსტის ველები და მდგომარეობის წარწერა."""
        tk.Label(parent, text="შეყვანა:", bg=BODY_COLOR, fg=TEXT_COLOR,
                 font=(FONT_FAMILY, 11)).pack(anchor="w")
        self._input_label = tk.Label(
            parent, bg=LAMP_OFF_BG, fg=TEXT_COLOR, font=CODE_FONT, anchor="w", justify="left",
            wraplength=WRAP_WIDTH, height=2,
        )
        self._input_label.pack(fill="x")

        tk.Label(parent, text="შედეგი:", bg=BODY_COLOR, fg=TEXT_COLOR,
                 font=(FONT_FAMILY, 11)).pack(anchor="w", pady=(6, 0))
        self._output_label = tk.Label(
            parent, bg=LAMP_OFF_BG, fg=LAMP_ON_BG, font=CODE_FONT, anchor="w", justify="left",
            wraplength=WRAP_WIDTH, height=2,
        )
        self._output_label.pack(fill="x")

        self._status_label = tk.Label(
            parent, bg=BODY_COLOR, fg=TEXT_COLOR, font=(FONT_FAMILY, 12, "bold"),
            wraplength=WRAP_WIDTH,
        )
        self._status_label.pack(pady=6)

    def _build_bottom_buttons(self, parent):
        """ქვედა ღილაკები: საწყისზე დაბრუნება, ავტომატური აკრეფა, უკან გაზეთზე."""
        row = tk.Frame(parent, bg=BODY_COLOR)
        row.pack(pady=(0, 8))
        tk.Button(
            row, text="საწყისზე დაბრუნება", font=(FONT_FAMILY, 10), command=self._reset,
        ).pack(side="left", padx=4)
        tk.Button(
            row, text="ავტომატურად ჩაწერე შეტყობინება", font=(FONT_FAMILY, 10),
            command=self._auto_type,
        ).pack(side="left", padx=4)
        if self._on_back is not None:
            tk.Button(
                row, text="← გაზეთზე", font=(FONT_FAMILY, 10), command=self._on_back,
            ).pack(side="left", padx=4)

    def _build_plugboard_panel(self, parent):
        """მარჯვენა პანელი: პლაგბორდის კაბელების დამატება/წაშლა."""
        panel = tk.Frame(parent, bg=PANEL_COLOR, padx=10, pady=10)
        panel.pack(side="right", fill="y", padx=(12, 0))

        tk.Label(panel, text="პლაგბორდი", bg=PANEL_COLOR, fg=TEXT_COLOR,
                 font=(FONT_FAMILY, 14, "bold")).pack()

        row = tk.Frame(panel, bg=PANEL_COLOR)
        row.pack(pady=8)
        one_char = (self.register(allow_one_char), "%P")
        self._plug_first = tk.StringVar()
        self._plug_second = tk.StringVar()
        tk.Entry(
            row, textvariable=self._plug_first, width=2, justify="center", font=CODE_FONT,
            validate="key", validatecommand=one_char,
        ).pack(side="left")
        tk.Label(row, text="↔", bg=PANEL_COLOR, fg=TEXT_COLOR,
                 font=(FONT_FAMILY, 14)).pack(side="left", padx=4)
        tk.Entry(
            row, textvariable=self._plug_second, width=2, justify="center", font=CODE_FONT,
            validate="key", validatecommand=one_char,
        ).pack(side="left")

        tk.Button(panel, text="დამატება", font=(FONT_FAMILY, 10), command=self._add_plug).pack()

        self._plug_list = tk.Listbox(panel, height=8, width=12, font=CODE_FONT, exportselection=False)
        self._plug_list.pack(pady=8)
        tk.Button(panel, text="მონიშნულის წაშლა", font=(FONT_FAMILY, 10),
                  command=self._remove_plug).pack()
        tk.Button(panel, text="ყველას წაშლა", font=(FONT_FAMILY, 10),
                  command=self._clear_plugs).pack(pady=4)

        self._plug_message = tk.Label(
            panel, bg=PANEL_COLOR, fg=BAD_COLOR, font=(FONT_FAMILY, 10), wraplength=190,
        )
        self._plug_message.pack(pady=4)
        tk.Label(
            panel, text="გაზეთის შეტყობინება პლაგბორდის გარეშეა დაშიფრული, ამიტომ კაბელებით "
                        "ის ვეღარ გაიშიფრება.",
            bg=PANEL_COLOR, fg=TEXT_COLOR, font=(FONT_FAMILY, 9), wraplength=190, justify="left",
        ).pack(pady=(8, 0))

    # --- ტექსტის აკრეფა და ნათურები ---
    def _press(self, letter):
        """ერთი ასოს დაჭერა: მანქანა აშიფრავს, ნათურა ინთება, ტექსტი განახლდება."""
        self._type_letter(letter)
        self._refresh()

    def _type_letter(self, letter):
        """შიფრავს ასოს და ამატებს შეყვანასა და შედეგს (ეკრანის განახლების გარეშე)."""
        lit = self._machine.encode_letter(letter)
        self._input_text += letter
        self._output_text += lit
        self._light_lamp(lit)

    def _add_space(self):
        """ინტერვალი მანქანას არ ატრიალებს: ორივე ტექსტში უბრალოდ ემატება."""
        self._input_text += " "
        self._output_text += " "
        self._refresh()

    def _auto_type(self):
        """ჯერ საწყისზე აბრუნებს მანქანას, მერე ავტომატურად აკრებს შიფრირებულ შეტყობინებას."""
        self._reset()
        for char in self._ciphertext:
            if char in ALPHABET:
                self._type_letter(char)
            else:
                self._input_text += char
                self._output_text += char
        self._refresh()

    def _light_lamp(self, letter):
        """ანთებს მოცემულ ასოს ნათურას და აყენებს გამორთვის ტაიმერს."""
        if self._lamp_job is not None:
            self.after_cancel(self._lamp_job)
            self._lamp_job = None
        self._dim_lamp()
        self._lamps[letter].config(bg=LAMP_ON_BG, fg=LAMP_ON_FG)
        self._lit_letter = letter
        self._lamp_job = self.after(LAMP_DURATION_MS, self._timer_off)

    def _timer_off(self):
        """ტაიმერის დასრულებისას აქრობს ნათურას."""
        self._lamp_job = None
        self._dim_lamp()

    def _dim_lamp(self):
        """აქრობს ახლა ანთებულ ნათურას (თუ არის)."""
        if self._lit_letter is not None:
            self._lamps[self._lit_letter].config(bg=LAMP_OFF_BG, fg=LAMP_OFF_FG)
            self._lit_letter = None

    def _on_key_event(self, event):
        """ნამდვილი კლავიატურის დაჭერა. პლაგბორდის ველებში აკრეფისას მანქანას არ ვატრიალებთ."""
        if isinstance(event.widget, (tk.Entry, tk.Listbox)):
            return
        if event.keysym == "space":
            if not isinstance(event.widget, tk.Button):
                self._add_space()
            return
        letter = event.char.upper()
        # ქართული ან სხვა სიმბოლოები უბრალოდ იგნორირდება
        if len(letter) == 1 and letter in ALPHABET:
            self._press(letter)

    # --- განახლება და საწყისზე დაბრუნება ---
    def _refresh(self):
        """განაახლებს როტორების ასოებს, ტექსტებს და გაშიფვრის სტატუსს."""
        for label, letter in zip(self._rotor_labels, self._machine.positions):
            label.config(text=letter)
        self._input_label.config(text=self._input_text)
        self._output_label.config(text=self._output_text)

        if self._is_solved():
            self._status_label.config(text="✔ შეტყობინება გაშიფრულია!", fg=GOOD_COLOR)
        else:
            self._status_label.config(text="", fg=TEXT_COLOR)

    def _is_solved(self):
        """True, თუ მიღებული ტექსტი (ინტერვალების გარეშე) უდრის საიდუმლო შეტყობინებას."""
        expected = self._article["message"].upper().replace(" ", "")
        received = self._output_text.replace(" ", "")
        return received == expected

    def _reset(self):
        """როტორებს აბრუნებს საწყის პოზიციაზე და ასუფთავებს ტექსტებს."""
        self._machine.positions = self._start_positions
        self._input_text = ""
        self._output_text = ""
        self._refresh()

    # --- პლაგბორდი ---
    def _add_plug(self):
        """ამატებს კაბელს. არასწორი მონაცემისას components.py აბრუნებს EnigmaError-ს."""
        try:
            self._machine.plugboard.add_pair(self._plug_first.get(), self._plug_second.get())
        except EnigmaError as error:
            self._plug_message.config(text=str(error))
            return
        self._plug_first.set("")
        self._plug_second.set("")
        self._after_plugboard_change()

    def _remove_plug(self):
        """შლის მონიშნულ კაბელს. Plugboard-ს ერთი წყვილის წაშლა არ აქვს, ამიტომ
        ვასუფთავებთ და დანარჩენ წყვილებს თავიდან ვამატებთ."""
        selection = self._plug_list.curselection()
        if not selection:
            self._plug_message.config(text="ჯერ მონიშნე კაბელი სიაში")
            return
        pairs = self._machine.plugboard.get_pairs()
        del pairs[selection[0]]
        self._machine.plugboard.clear()
        for first, second in pairs:
            self._machine.plugboard.add_pair(first, second)
        self._after_plugboard_change()

    def _clear_plugs(self):
        """შლის ყველა კაბელს."""
        self._machine.plugboard.clear()
        self._after_plugboard_change()

    def _after_plugboard_change(self):
        """პლაგბორდის ცვლილების შემდეგ ვაახლებთ სიას და მანქანას საწყისზე ვაბრუნებთ,
        რადგან ძველი შედეგები ახალ კაბელებს აღარ შეესაბამება."""
        self._plug_message.config(text="")
        self._plug_list.delete(0, "end")
        for first, second in self._machine.plugboard.get_pairs():
            self._plug_list.insert("end", f"{first} ↔ {second}")
        self._reset()

    # --- გასუფთავება ---
    def destroy(self):
        """ეკრანის დახურვისას ვხსნით კლავიატურის მოსმენას და ტაიმერს."""
        try:
            self.winfo_toplevel().unbind("<Key>", self._key_binding)
            if self._lamp_job is not None:
                self.after_cancel(self._lamp_job)
        except tk.TclError:
            pass  # ფანჯარა უკვე დახურულია
        super().destroy()
