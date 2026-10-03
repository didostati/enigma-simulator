"""
machine.py - ენიგმას სრული მანქანა.

აერთიანებს components.py-ის კომპონენტებს (პლაგბორდი, 3 როტორი, რეფლექტორი)
ერთ კლასში - EnigmaMachine.

სიგნალის გზა ერთი ასოსთვის:
    კლავიში -> პლაგბორდი -> მარჯვენა როტორი -> შუა -> მარცხენა -> რეფლექტორი
            -> მარცხენა -> შუა -> მარჯვენა -> პლაგბორდი -> ნათურა
"""

from enigma.components import (
    ALPHABET,
    EnigmaError,
    Plugboard,
    Reflector,
    create_rotor,
    index_to_letter,
    letter_to_index,
)


class EnigmaMachine:
    """ენიგმას მანქანა: ასოებს და ტექსტს შიფრავს/გაშიფრავს."""

    def __init__(self, rotor_names=("I", "II", "III"), positions="AAA", plugboard=None):
        # როტორების სახელები მარცხნიდან მარჯვნივ; განმეორება აკრძალულია
        if len(rotor_names) != 3 or len(set(rotor_names)) != 3:
            raise EnigmaError("საჭიროა 3 განსხვავებული როტორი")

        # create_rotor თვითონ ამოწმებს, არსებობს თუ არა ასეთი სახელი
        self._rotors = [create_rotor(name) for name in rotor_names]
        self._reflector = Reflector()
        self._plugboard = plugboard if plugboard is not None else Plugboard()
        self.positions = positions  # გაივლის setter-ის ვალიდაციას

    # --- პოზიციები (ინკაფსულაცია: სამივე როტორი ერთ სტრიქონად) ---
    @property
    def positions(self):
        """როტორების მიმდინარე პოზიციები მარცხნიდან მარჯვნივ, მაგ. 'AAA'."""
        return "".join(rotor.position for rotor in self._rotors)

    @positions.setter
    def positions(self, value):
        if not isinstance(value, str) or len(value) != 3:
            raise EnigmaError("საწყისი პოზიცია უნდა იყოს 3 ასო, მაგ. 'ABC'")
        # ჯერ ვამოწმებთ ყველა ასოს, რომ შეცდომისას ნახევრად არ შეიცვალოს
        for letter in value:
            letter_to_index(letter)
        for rotor, letter in zip(self._rotors, value):
            rotor.position = letter

    @property
    def plugboard(self):
        """წვდომა პლაგბორდზე (კაბელების დასამატებლად)."""
        return self._plugboard

    def _step_rotors(self):
        """როტორების ბრუნვა ყოველი კლავიშის დაჭერისას (double-stepping-ის ჩათვლით)."""
        left, middle, right = self._rotors

        if middle.at_notch():
            # შუა როტორი notch-ზეა: ორივე, მარცხენაც და შუაც, ერთად ბრუნავს
            left.step()
            middle.step()
        elif right.at_notch():
            # მარჯვენა notch-ზეა: შუა როტორიც მიჰყვება
            middle.step()
        # მარჯვენა როტორი ბრუნავს ყოველთვის
        right.step()

    def encode_letter(self, letter):
        """შიფრავს ერთ ასოს. ჯერ როტორები ბრუნავს, მერე სიგნალი გადის წრეს."""
        index = letter_to_index(letter)
        self._step_rotors()

        left, middle, right = self._rotors

        index = self._plugboard.encode(index)
        # წინა მიმართულება: მარჯვნიდან მარცხნივ
        index = right.encode_forward(index)
        index = middle.encode_forward(index)
        index = left.encode_forward(index)
        # რეფლექტორი
        index = self._reflector.encode(index)
        # უკან: მარცხნიდან მარჯვნივ
        index = left.encode_backward(index)
        index = middle.encode_backward(index)
        index = right.encode_backward(index)
        index = self._plugboard.encode(index)

        return index_to_letter(index)

    def encode_text(self, text):
        """შიფრავს ტექსტს. ლათინური ასოები იშიფრება, დანარჩენი (ინტერვალი, პუნქტუაცია) უცვლელი რჩება."""
        result = []
        for char in text:
            if char.upper() in ALPHABET:
                result.append(self.encode_letter(char))
            else:
                result.append(char)
        return "".join(result)


# ამ ფაილის პირდაპირი გაშვებისას - თვითშემოწმება
if __name__ == "__main__":
    # 1) ცნობილი ტესტი: I-II-III, პოზიცია AAA, ხუთი A -> BDZGO
    machine = EnigmaMachine()
    encrypted = machine.encode_text("AAAAA")
    print("AAAAA ->", encrypted, "(მოსალოდნელია BDZGO)")

    # 2) გაშიფვრა = იგივე პარამეტრებით ხელახლა შიფრვა
    machine = EnigmaMachine()
    print("BDZGO ->", machine.encode_text(encrypted), "(მოსალოდნელია AAAAA)")

    # 3) double-stepping: ADU -> (3 ასო) -> BFX
    machine = EnigmaMachine(positions="ADU")
    machine.encode_text("AAA")
    print("ADU + 3 ასო ->", machine.positions, "(მოსალოდნელია BFX)")

    # 4) პლაგბორდით და ტექსტით: შიფრვა, მერე გაშიფვრა
    message = "HELLO WORLD"
    machine = EnigmaMachine(("II", "I", "III"), "XYZ")
    machine.plugboard.add_pair("H", "E")
    machine.plugboard.add_pair("L", "O")
    secret = machine.encode_text(message)

    machine = EnigmaMachine(("II", "I", "III"), "XYZ")
    machine.plugboard.add_pair("H", "E")
    machine.plugboard.add_pair("L", "O")
    print(message, "->", secret, "->", machine.encode_text(secret))
