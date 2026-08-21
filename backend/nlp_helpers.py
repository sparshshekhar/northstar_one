import re

DEVANAGARI_RE = re.compile(r'[\u0900-\u097F]')

HINGLISH_HINTS = {
    "hai", "hain", "hoga", "hogi", "honge", "tha", "thi", "the", "kya", "kyu", "kyun", "kyunki", "kaise", "kaisa", "kaisi", "kitna", "kitne", "kitni", "kab", "kaha", "kahan", "kaunsa", "konsa",
    "nahi", "nahin", "haan", "ha", "accha", "acha", "theek", "thik",
    "chahiye", "zaroorat", "zarurat", "matlab", "bhai", "yaar", "sir", "madam", "aap", "aapka", "aapki", "aapke",
    "mera", "meri", "mere", "mujhe", "hamara", "hamari", "hamen",
    "kar", "karo", "karna", "kardo", "kar do", "kijiye", "kijiyega",
    "batao", "bataiye", "dijiye", "dedo", "de do", "lelo", "le lo", "rakho", "rakhna", "milega", "milegi", "milte", "milta", "chalega", "chalegi", "chaliye", "chalo", "abhi", "kal", "aaj", "parso", "subah", "shaam", "raat", "din", "wala", "wale", "wali", "aur", "lekin", "phir", "fir", "toh", "to", "sector", "ghar", "flat", "dekhna", "dekhlo", "dekh lo", "krna", "krdo", "kro", "krlo", "kr lo", "kro na", "plz", "pls", "bata", "bta", "bhi", "hi", "sath", "saath", "jaldi", "der", "turant", "zyada", "kam", "thoda", "thodi", "vaise", "kuchh", "kuch", "yah", "ye", "yeh", "koi", "galat", "sahi", "sahi hai", "hata", "hatao", "hata do", "wala zero", "number",
}

CLOSING_HINTS_EXACT = [
    "thank you", "thankyou", "thanku", "thanks", "thank u", "thnx", "tysm", "tq",
    "no more questions", "that's all", "thats all", "bye", "goodbye", "ok bye",
    "धन्यवाद", "शुक्रिया", "अलविदा", "थैंक यू", "थैंक्स",
    "shukriya", "alvida", "koi aur sawal nahi", "bas itna hi", "chalta hoon", "chalti hoon", "nahi chahiye abhi",
]

DHANYAVAD_RE = re.compile(r"dh?any[a-z]{0,3}v?[a]?[a]?d", re.IGNORECASE)


def detect_language(text: str) -> str:
    """Returns 'hindi', 'hinglish', or 'english' based on the user's message."""
    if DEVANAGARI_RE.search(text):
        return "hindi"
    words = set(re.findall(r"[a-zA-Z]+", text.lower()))
    if words & HINGLISH_HINTS:
        return "hinglish"
    return "english"


def is_closing_message(text: str) -> bool:
    """Detects goodbye/thank-you signals directly from the customer's own
    words, in English, Hindi, or Hinglish spelling variants — doesn't rely
    on the model remembering to flag it."""
    t = text.lower()
    if any(kw in t for kw in CLOSING_HINTS_EXACT):
        return True
    if DHANYAVAD_RE.search(t):
        return True
    return False