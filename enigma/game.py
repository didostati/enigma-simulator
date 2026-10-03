"""
game.py - გაზეთის თამაშის ლოგიკა.

თამაშის იდეა:
    1. მოთამაშეს ეძლევა ძველი გაზეთის სტატია და შიფრირებული შეტყობინება.
    2. ენიგმა სწორად იმუშავებს მხოლოდ მაშინ, თუ მოთამაშე გამოიცნობს
       სტატიაში დამალულ საკვანძო სიტყვას (ე.წ. "crib").
    3. გამოცნობილი სიტყვის პირველი სამი ასო ხდება როტორების საწყისი პოზიცია.
    4. სწორი სიტყვისას მანქანა შეტყობინებას წაკითხვადად გაშიფრავს,
       არასწორისას - უაზრო ასოებს მივიღებთ.

ფაილში არის მხოლოდ ფუნქციები (არ არის UI): მონაცემების ჩატვირთვა,
ვალიდაცია, გასაღების გამოყვანა, შიფრვა/გაშიფვრა და ერთი რაუნდის ჩატარება.
"""

import json
import os
import random

from enigma.components import ALPHABET, EnigmaError
from enigma.machine import EnigmaMachine

# გზა data/newspaper.json-მდე (პროექტის ძირითად ფოლდერთან შედარებით)
PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_PATH = os.path.join(PROJECT_DIR, "data", "newspaper.json")

# სტატიის ყველა სავალდებულო ველი
REQUIRED_KEYS = ("title", "text", "secret_word", "message")

# თამაშში გამოყენებული როტორები (მარცხნიდან მარჯვნივ)
DEFAULT_ROTORS = ("I", "II", "III")

# რამდენი მცდელობა აქვს მოთამაშეს ერთ რაუნდში
MAX_ATTEMPTS = 3


def extract_words(text):
    """ტექსტიდან იღებს სიტყვების სიას დიდი ასოებით, მაგ. 'Hi, you!' -> ['HI', 'YOU']."""
    cleaned = ""
    for char in text.upper():
        # ლათინური ასო ინახება, ყველა დანარჩენი (პუნქტუაცია, ციფრი) ინტერვალით იცვლება
        if char in ALPHABET:
            cleaned += char
        else:
            cleaned += " "
    return cleaned.split()


def key_from_word(word):
    """სიტყვიდან აგებს როტორების საწყის პოზიციას (პირველი 3 ასო).
    არასწორი მონაცემისას იძლევა EnigmaError-ს."""
    if not isinstance(word, str):
        raise EnigmaError("სიტყვა უნდა იყოს ტექსტი")

    word = word.strip().upper()
    if len(word) < 3:
        raise EnigmaError("სიტყვა მინიმუმ 3 ასოს უნდა შეიცავდეს")
    for char in word:
        if char not in ALPHABET:
            raise EnigmaError("დაშვებულია მხოლოდ ლათინური ასოები A-Z (ციფრების და ნიშნების გარეშე)")

    return word[:3]


def validate_article(article, index):
    """ამოწმებს ერთ სტატიას: ყველა ველი არსებობს, საკვანძო სიტყვა ტექსტშია, შეტყობინება სწორია."""
    if not isinstance(article, dict):
        raise EnigmaError(f"სტატია №{index}: უნდა იყოს ობიექტი (ლექსიკონი)")

    for key in REQUIRED_KEYS:
        value = article.get(key)
        if not isinstance(value, str) or not value.strip():
            raise EnigmaError(f"სტატია №{index}: ველი {key!r} აკლია ან ცარიელია")

    # საკვანძო სიტყვა უნდა იყოს სწორი და რეალურად შედიოდეს სტატიის ტექსტში
    key_from_word(article["secret_word"])
    if article["secret_word"].upper() not in extract_words(article["text"]):
        raise EnigmaError(f"სტატია №{index}: საკვანძო სიტყვა ტექსტში არ გვხვდება")

    # შეტყობინებაში მხოლოდ ასოები და ინტერვალებია დაშვებული
    for char in article["message"].upper():
        if char != " " and char not in ALPHABET:
            raise EnigmaError(f"სტატია №{index}: შეტყობინებაში დაშვებულია მხოლოდ A-Z და ინტერვალი")


def load_articles(path=DATA_PATH):
    """კითხულობს სტატიებს JSON ფაილიდან და ამოწმებს თითოეულს. აბრუნებს სტატიების სიას."""
    try:
        with open(path, "r", encoding="utf-8") as file:
            articles = json.load(file)
    except FileNotFoundError:
        raise EnigmaError(f"ფაილი ვერ მოიძებნა: {path}")
    except json.JSONDecodeError as error:
        raise EnigmaError(f"JSON ფაილი დაზიანებულია: {error}")

    if not isinstance(articles, list) or len(articles) == 0:
        raise EnigmaError("ფაილში უნდა იყოს სტატიების არაცარიელი სია")

    for index, article in enumerate(articles, start=1):
        validate_article(article, index)

    return articles


def pick_article(articles):
    """შემთხვევითად ირჩევს ერთ სტატიას სიიდან."""
    return random.choice(articles)


def encrypt_message(article, rotor_names=DEFAULT_ROTORS):
    """აშიფრავს სტატიის საიდუმლო შეტყობინებას; გასაღები არის საკვანძო სიტყვის პირველი 3 ასო."""
    machine = EnigmaMachine(rotor_names, key_from_word(article["secret_word"]))
    return machine.encode_text(article["message"].upper())


def check_guess(article, guess, rotor_names=DEFAULT_ROTORS):
    """ამოწმებს მოთამაშის ვარაუდს.
    აბრუნებს წყვილს: (გაშიფრული ტექსტი, წარმატებულია თუ არა)."""
    ciphertext = encrypt_message(article, rotor_names)
    machine = EnigmaMachine(rotor_names, key_from_word(guess))
    decrypted = machine.encode_text(ciphertext)
    return decrypted, decrypted == article["message"].upper()


def play_round(articles, max_attempts=MAX_ATTEMPTS):
    """ატარებს ერთ რაუნდს კონსოლში. აბრუნებს True-ს, თუ მოთამაშემ გამოიცნო."""
    article = pick_article(articles)

    print("=" * 50)
    print(article["title"])
    print(article["text"])
    print("=" * 50)
    print("შიფრირებული შეტყობინება:", encrypt_message(article))
    print("იპოვე სტატიაში საკვანძო სიტყვა!")

    attempts_left = max_attempts
    while attempts_left > 0:
        guess = input(f"შენი ვარაუდი (დარჩენილია {attempts_left} მცდელობა): ")

        try:
            decrypted, success = check_guess(article, guess)
        except EnigmaError as error:
            # არასწორი შეყვანა მცდელობას არ ხარჯავს
            print("შეცდომა:", error)
            continue

        if success:
            print("სწორია! მანქანამ გაშიფრა:", decrypted)
            return True

        attempts_left -= 1
        print("მანქანამ გაშიფრა:", decrypted, "- უაზრობაა, სცადე თავიდან")

    print("მცდელობები ამოიწურა. საკვანძო სიტყვა იყო:", article["secret_word"])
    return False


def run_self_test(articles):
    """ავტომატური შემოწმება: ყველა სტატია სწორი სიტყვით იხსნება, არასწორით - არა."""
    print("სტატიების რაოდენობა:", len(articles))

    for article in articles:
        _, ok = check_guess(article, article["secret_word"])
        _, bad = check_guess(article, "ZZZZ")
        print(f"{article['title']}: სწორი სიტყვა -> {ok} (მოსალოდნელია True), 'ZZZZ' -> {bad} (მოსალოდნელია False)")

    try:
        key_from_word("ab")
    except EnigmaError as error:
        print("ვალიდაცია მუშაობს:", error)


# ამ ფაილის პირდაპირი გაშვებისას: ჯერ თვითშემოწმება, მერე ერთი რაუნდი
if __name__ == "__main__":
    try:
        loaded = load_articles()
    except EnigmaError as error:
        print("ჩატვირთვის შეცდომა:", error)
    else:
        run_self_test(loaded)
        print()
        play_round(loaded)
