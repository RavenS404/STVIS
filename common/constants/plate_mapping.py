# ── Arabic character mapping for Egyptian license plates ──────────────
# Maps YOLO model class names → Arabic display characters.
# Model classes (27): 1-9 digits, alf, ba2, dal, ein, fa2, gem, ha, ha2,
#                      lam, mem, non, qaf, ra2, sad, sen, ta2, waw, ya2

ARABIC_MAP = {
    # Letters
    "alf": "ا",
    "ba2": "ب",
    "gem": "ج",
    "dal": "د",
    "ra2": "ر",
    "sen": "س",
    "sad": "ص",
    "ta2": "ط",
    "ein": "ع",
    "fa2": "ف",
    "qaf": "ق",
    "lam": "ل",
    "mem": "م",
    "non": "ن",
    "ha2": "ه",
    "waw": "و",
    "ya2": "ي",
    # Digits → Eastern Arabic numerals
    "1": "١",
    "2": "٢",
    "3": "٣",
    "4": "٤",
    "5": "٥",
    "6": "٦",
    "7": "٧",
    "8": "٨",
    "9": "٩",
}

# Model class 15 is "ha" — treat as alias for "ha2"
PLATE_CLASS_ALIASES = {
    "one": "1",
    "two": "2",
    "three": "3",
    "four": "4",
    "five": "5",
    "six": "6",
    "seven": "7",
    "eight": "8",
    "nine": "9",
    "baa": "ba2",
    "faa": "fa2",
    "haa": "ha2",
    "ha": "ha2",
    "raa": "ra2",
    "taa": "ta2",
    "yaa": "ya2",
}

# Character type sets for sorting and validation
LETTER_CLASSES = frozenset({
    "alf", "ba2", "gem", "dal", "ra2", "sen", "sad", "ta2",
    "ein", "fa2", "qaf", "lam", "mem", "non", "ha", "ha2",
    "waw", "ya2",
})

DIGIT_CLASSES = frozenset({"1", "2", "3", "4", "5", "6", "7", "8", "9"})

# Classes the model may output that are NOT plate characters
IGNORED_CLASSES = frozenset({"background"})
