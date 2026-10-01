"""
components.py - ენიგმას მანქანის ძირითადი კომპონენტები.

შეიცავს:
    - Component   : საბაზო კლასი (ყველა კომპონენტის საერთო "ინტერფეისი")
    - Plugboard   : კომუტაციის დაფა (ასოების წყვილების გაცვლა)
    - Rotor       : როტორი (ბრუნავს და ასოებს გადაადგილებს)
    - Reflector   : რეფლექტორი (სიგნალს უკან აბრუნებს)
    - create_rotor: ფუნქცია, რომელიც ისტორიული როტორის შექმნას აადვილებს

OOP პრინციპები ამ ფაილში:
    - ინკაფსულაცია : შიდა მონაცემები იწყება "_"-ით (მაგ. self._position)
                      და იცვლება მხოლოდ კონტროლირებადი მეთოდებით/property-ით.
    - მემკვიდრეობა : Plugboard, Rotor და Reflector მემკვიდრეობით იღებენ Component-ს.
    - პოლიმორფიზმი : ყველა კლასს აქვს encode(index) მეთოდი, მაგრამ
                      თითოეული მას თავისებურად ახორციელებს.
"""

# ანბანი: ასოს ინდექსი (A=0 ... Z=25) გვჭირდება გამოთვლებისთვის
ALPHABET = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
ALPHABET_SIZE = len(ALPHABET)

# ისტორიული როტორების გაყვანილობა და "notch" ასო
# (notch - ის ასო, რომელზეც როტორი შემდეგ როტორსაც ატრიალებს)
ROTOR_SPECS = {
    "I": ("EKMFLGDQVZNTOWYHXUSPAIBRCJ", "Q"),
    "II": ("AJDKSIRUXBLHWTMCQGZNPYFVOE", "E"),
    "III": ("BDFHJLCPRTXVZNYEIGAMWUSKQO", "V"),
}

# რეფლექტორი B (ყველაზე გავრცელებული)
REFLECTOR_B_WIRING = "YRUHQSLDPXNGOKMIEBFZCWVJAT"

# პლაგბორდზე მაქსიმუმ 10 კაბელი იყო
MAX_PLUG_PAIRS = 10


class EnigmaError(Exception):
    """ჩვენი პროექტის საკუთარი შეცდომა არასწორი მონაცემებისთვის."""


def letter_to_index(letter):
    """გადაჰყავს ასო ინდექსად: 'A' -> 0, 'Z' -> 25. არასწორ შემთხვევაში იძლევა შეცდომას."""
    if not isinstance(letter, str) or len(letter) != 1:
        raise EnigmaError(f"საჭიროა ერთი ასო, მივიღეთ: {letter!r}")
    letter = letter.upper()
    if letter not in ALPHABET:
        raise EnigmaError(f"დაშვებულია მხოლოდ ლათინური ასოები A-Z, მივიღეთ: {letter!r}")
    return ALPHABET.index(letter)


def index_to_letter(index):
    """გადაჰყავს ინდექსი ასოდ: 0 -> 'A', 25 -> 'Z'."""
    return ALPHABET[index % ALPHABET_SIZE]


def validate_wiring(wiring):
    """ამოწმებს, რომ გაყვანილობა არის 26 განსხვავებული ლათინური ასო."""
    if len(wiring) != ALPHABET_SIZE or sorted(wiring.upper()) != list(ALPHABET):
        raise EnigmaError("გაყვანილობა უნდა შეიცავდეს ანბანის ყველა 26 ასოს ზუსტად ერთხელ")
    return wiring.upper()


class Component:
    """საბაზო კლასი. ყველა კომპონენტს უნდა ჰქონდეს encode მეთოდი."""

    def encode(self, index):
        """იღებს ასოს ინდექსს (0-25) და აბრუნებს გარდაქმნილ ინდექსს.
        საბაზო კლასში არ არის რეალიზებული - მემკვიდრეებმა უნდა გადაფარონ."""
        raise NotImplementedError("encode() უნდა განისაზღვროს მემკვიდრე კლასში")


class Plugboard(Component):
    """კომუტაციის დაფა: აცვლის ასოების წყვილებს (მაგ. A<->B)."""

    def __init__(self):
        # ლექსიკონი: თითოეული ასო -> მისი წყვილი (ორივე მიმართულებით)
        self._pairs = {}

    def add_pair(self, first, second):
        """ამატებს კაბელს ორ ასოს შორის (ვალიდაციით)."""
        first = index_to_letter(letter_to_index(first))
        second = index_to_letter(letter_to_index(second))

        if first == second:
            raise EnigmaError("ასო საკუთარ თავთან ვერ შეერთდება")
        if first in self._pairs or second in self._pairs:
            raise EnigmaError("ერთი ასო მხოლოდ ერთ კაბელში შეიძლება იყოს")
        if len(self._pairs) // 2 >= MAX_PLUG_PAIRS:
            raise EnigmaError(f"მაქსიმუმ {MAX_PLUG_PAIRS} კაბელია დაშვებული")

        self._pairs[first] = second
        self._pairs[second] = first

    def clear(self):
        """შლის ყველა კაბელს."""
        self._pairs.clear()

    def get_pairs(self):
        """აბრუნებს წყვილების სიას (თითო წყვილი ერთხელ), მაგ. [('A','B')]."""
        return sorted({tuple(sorted(item)) for item in self._pairs.items()})

    def encode(self, index):
        """თუ ასოს აქვს წყვილი - ცვლის მას, თუ არა - უცვლელად ტოვებს."""
        letter = index_to_letter(index)
        return letter_to_index(self._pairs.get(letter, letter))


class Rotor(Component):
    """როტორი: ასოებს გადაადგილებს თავისი გაყვანილობით და ბრუნვისას თავის პოზიციას ცვლის."""

    def __init__(self, name, wiring, notch, position="A"):
        self._name = name
        self._wiring = validate_wiring(wiring)
        self._notch = index_to_letter(letter_to_index(notch))
        self._position = 0
        self.position = position  # გაივლის setter-ის ვალიდაციას

    # --- property: კონტროლირებადი წვდომა პოზიციაზე (ინკაფსულაცია) ---
    @property
    def name(self):
        return self._name

    @property
    def position(self):
        """მიმდინარე პოზიცია ასოდ (A-Z)."""
        return index_to_letter(self._position)

    @position.setter
    def position(self, letter):
        self._position = letter_to_index(letter)

    def at_notch(self):
        """True, თუ როტორი ახლა notch-ის პოზიციაზეა (შემდეგ როტორსაც ატრიალებს)."""
        return self.position == self._notch

    def step(self):
        """როტორს ერთი ნაბიჯით ატრიალებს."""
        self._position = (self._position + 1) % ALPHABET_SIZE

    def encode_forward(self, index):
        """სიგნალი მიდის პლაგბორდიდან რეფლექტორისკენ."""
        shifted = (index + self._position) % ALPHABET_SIZE
        output = ALPHABET.index(self._wiring[shifted])
        return (output - self._position) % ALPHABET_SIZE

    def encode_backward(self, index):
        """სიგნალი ბრუნდება რეფლექტორიდან უკან (შებრუნებული გაყვანილობით)."""
        shifted = (index + self._position) % ALPHABET_SIZE
        output = self._wiring.index(ALPHABET[shifted])
        return (output - self._position) % ALPHABET_SIZE

    def encode(self, index):
        """პოლიმორფიზმი: ზოგადი encode ჩვენთვის წინა მიმართულებაა."""
        return self.encode_forward(index)


class Reflector(Component):
    """რეფლექტორი: სიგნალს უკან აბრუნებს. ასო არასდროს აისახება თავის თავში."""

    def __init__(self, wiring=REFLECTOR_B_WIRING):
        self._wiring = validate_wiring(wiring)
        # რეფლექტორი უნდა იყოს წყვილებად: თუ A->Y, მაშინ Y->A და არცერთი ასო არ რჩება თავის ადგილას
        for i, letter in enumerate(self._wiring):
            partner = self._wiring[ALPHABET.index(letter)]
            if letter == ALPHABET[i] or partner != ALPHABET[i]:
                raise EnigmaError("რეფლექტორი უნდა შედგებოდეს ასოების წყვილებისგან")

    def encode(self, index):
        return ALPHABET.index(self._wiring[index])


def create_rotor(name, position="A"):
    """ქმნის ისტორიულ როტორს სახელით ("I", "II", "III")."""
    if name not in ROTOR_SPECS:
        raise EnigmaError(f"უცნობი როტორი {name!r}. ხელმისაწვდომია: {', '.join(ROTOR_SPECS)}")
    wiring, notch = ROTOR_SPECS[name]
    return Rotor(name, wiring, notch, position)


# ამ ფაილის პირდაპირი გაშვებისას - მცირე თვითშემოწმება
if __name__ == "__main__":
    rotor = create_rotor("I")
    print("როტორი I, პოზიცია A: A ->", index_to_letter(rotor.encode_forward(0)), "(მოსალოდნელია E)")
    print("უკან: E ->", index_to_letter(rotor.encode_backward(4)), "(მოსალოდნელია A)")

    reflector = Reflector()
    print("რეფლექტორი B: A ->", index_to_letter(reflector.encode(0)), "(მოსალოდნელია Y)")

    board = Plugboard()
    board.add_pair("A", "B")
    print("პლაგბორდი A<->B: A ->", index_to_letter(board.encode(0)), "(მოსალოდნელია B)")

    try:
        board.add_pair("A", "C")
    except EnigmaError as error:
        print("ვალიდაცია მუშაობს:", error)




























