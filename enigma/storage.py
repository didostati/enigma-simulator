"""
storage.py - თამაშის შედეგების შენახვა ფაილში.
 
ფაილში არის მხოლოდ ფუნქციები (არ არის UI). ფაილებთან მუშაობის სამი ოპერაცია:
    - შექმნა/რედაქტირება: save_result (ფაილს ქმნის, თუ არ არსებობს, ან ახალ ჩანაწერს ამატებს);
    - წაკითხვა:           load_results;
    - წაშლა:              delete_result (ერთი ჩანაწერი) და clear_results (მთელი ფაილი).
 
შედეგები ინახება data/saves/results.json-ში (ეს ფოლდერი .gitignore-შია).
ერთი ჩანაწერი ლექსიკონია: time, title, guess, success, attempts_left.
"""
 
import json
import os
import tempfile
from datetime import datetime
 
from enigma.components import EnigmaError
 
# გზა data/saves/results.json-მდე (პროექტის ძირითად ფოლდერთან შედარებით)
PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RESULTS_PATH = os.path.join(PROJECT_DIR, "data", "saves", "results.json")
 
# დროის ფორმატი ჩანაწერებში
TIME_FORMAT = "%Y-%m-%d %H:%M"
 
 
def ensure_saves_dir(path=RESULTS_PATH):
    """ქმნის ფოლდერს, სადაც ფაილი ინახება, თუ ის ჯერ არ არსებობს."""
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
    except OSError as error:
        raise EnigmaError(f"ფოლდერის შექმნა ვერ მოხერხდა: {error}")
 
 
def load_results(path=RESULTS_PATH):
    """კითხულობს შედეგების სიას ფაილიდან.
    თუ ფაილი ჯერ არ არსებობს, აბრუნებს ცარიელ სიას; დაზიანებულ ფაილზე იძლევა EnigmaError-ს."""
    if not os.path.exists(path):
        return []
 
    try:
        with open(path, "r", encoding="utf-8") as file:
            results = json.load(file)
    except json.JSONDecodeError as error:
        raise EnigmaError(f"შედეგების ფაილი დაზიანებულია: {error}")
    except OSError as error:
        raise EnigmaError(f"ფაილის წაკითხვა ვერ მოხერხდა: {error}")
 
    if not isinstance(results, list):
        raise EnigmaError("შედეგების ფაილში უნდა იყოს ჩანაწერების სია")
 
    return results
 
 
def _write_results(results, path):
    """ინახავს მთელ სიას ფაილში (ძველი შიგთავსი იცვლება). შიდა დამხმარე ფუნქციაა."""
    ensure_saves_dir(path)
    try:
        with open(path, "w", encoding="utf-8") as file:
            json.dump(results, file, ensure_ascii=False, indent=2)
    except OSError as error:
        raise EnigmaError(f"ფაილში ჩაწერა ვერ მოხერხდა: {error}")
 
 
def save_result(title, guess, success, attempts_left, path=RESULTS_PATH):
    """ამატებს ერთ შედეგს ფაილში (ფაილს ქმნის, თუ ის არ არსებობს). აბრუნებს დამატებულ ჩანაწერს."""
    # ვალიდაცია: არასწორი მონაცემი ფაილში არ უნდა მოხვდეს
    if not isinstance(title, str) or not title.strip():
        raise EnigmaError("სათაური უნდა იყოს არაცარიელი ტექსტი")
    if not isinstance(guess, str):
        raise EnigmaError("ვარაუდი უნდა იყოს ტექსტი")
    if not isinstance(success, bool):
        raise EnigmaError("success უნდა იყოს True ან False")
    if isinstance(attempts_left, bool) or not isinstance(attempts_left, int) or attempts_left < 0:
        raise EnigmaError("დარჩენილი მცდელობები უნდა იყოს არაუარყოფითი მთელი რიცხვი")
 
    record = {
        "time": datetime.now().strftime(TIME_FORMAT),
        "title": title.strip(),
        "guess": guess.strip().upper(),
        "success": success,
        "attempts_left": attempts_left,
    }
 
    results = load_results(path)
    results.append(record)
    _write_results(results, path)
    return record
 
 
def delete_result(index, path=RESULTS_PATH):
    """შლის ერთ ჩანაწერს ნომრით (0-დან იწყება). აბრუნებს წაშლილ ჩანაწერს."""
    results = load_results(path)
 
    if isinstance(index, bool) or not isinstance(index, int):
        raise EnigmaError("ჩანაწერის ნომერი უნდა იყოს მთელი რიცხვი")
    if index < 0 or index >= len(results):
        raise EnigmaError(f"ასეთი ჩანაწერი არ არსებობს: {index}")
 
    removed = results.pop(index)
    _write_results(results, path)
    return removed
 
 
def clear_results(path=RESULTS_PATH):
    """შლის შედეგების ფაილს მთლიანად. აბრუნებს True-ს, თუ ფაილი იყო და წაიშალა."""
    if not os.path.exists(path):
        return False
 
    try:
        os.remove(path)
    except OSError as error:
        raise EnigmaError(f"ფაილის წაშლა ვერ მოხერხდა: {error}")
    return True
 
 
def format_result(result):
    """აქცევს ერთ ჩანაწერს ერთ სტრიქონად ეკრანზე ჩვენებისთვის."""
    verdict = "სწორია" if result["success"] else "არასწორია"
    return (
        f"{result['time']} | {result['title']} | {result['guess']} | "
        f"{verdict} | დარჩა {result['attempts_left']} მცდელობა"
    )
 
 
def run_self_test():
    """ავტომატური შემოწმება დროებით ფაილზე (რეალური შედეგები არ ზიანდება)."""
    with tempfile.TemporaryDirectory() as folder:
        path = os.path.join(folder, "saves", "results.json")
 
        print("ფაილის გარეშე სია ცარიელია:", load_results(path) == [])
 
        save_result("HARBOR NEWS", "tide", True, 2, path)
        save_result("WEATHER REPORT", "SNAW", False, 0, path)
        results = load_results(path)
        print("ორი ჩანაწერი შეინახა:", len(results) == 2)
        print("ვარაუდი დიდი ასოებითაა:", results[0]["guess"] == "TIDE")
        print(format_result(results[1]))
 
        removed = delete_result(0, path)
        print("წაიშალა პირველი:", removed["title"] == "HARBOR NEWS", "| დარჩა:", len(load_results(path)))
 
        try:
            delete_result(5, path)
        except EnigmaError as error:
            print("ვალიდაცია მუშაობს (ნომერი):", error)
 
        try:
            save_result("", "ABC", True, 1, path)
        except EnigmaError as error:
            print("ვალიდაცია მუშაობს (სათაური):", error)
 
        print("ფაილი წაიშალა:", clear_results(path), "| მეორედ:", clear_results(path))
 
 
# ამ ფაილის გაშვება პროექტის ძირითადი ფოლდერიდან:  python -m enigma.storage
if __name__ == "__main__":
    run_self_test()
