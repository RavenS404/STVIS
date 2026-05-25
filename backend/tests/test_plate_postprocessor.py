"""Tests for the plate post-processing pipeline."""

from common.utils.plate_reading import reconstruct_plate


# ── A. Digit + letter tokens are sorted correctly (Egyptian convention) ──

def test_letters_before_digits_in_display():
    """Letters come first, then digits, both sorted right-to-left."""
    result = reconstruct_plate(
        [
            {"label": "1", "confidence": 0.95, "bbox": [10, 10, 20, 30]},
            {"label": "2", "confidence": 0.92, "bbox": [25, 10, 35, 30]},
            {"label": "alf", "confidence": 0.88, "bbox": [40, 10, 52, 30]},
            {"label": "ba2", "confidence": 0.87, "bbox": [55, 10, 67, 30]},
        ]
    )
    assert result.letters_ar == "با"
    assert result.digits_ar == "٢١"
    assert result.display_summary_ar == "با ٢١"


# ── B. Unknown class returns UNKNOWN_CLASS and does not enter text ──

def test_unknown_class_triggers_uncertain_result():
    """A class not in ARABIC_MAP must produce 'نتيجة غير مؤكدة'."""
    result = reconstruct_plate(
        [
            {"label": "1", "confidence": 0.90, "bbox": [10, 10, 20, 30]},
            {"label": "2", "confidence": 0.92, "bbox": [25, 10, 35, 30]},
            {"label": "alf", "confidence": 0.88, "bbox": [40, 10, 52, 30]},
            {"label": "FAKE_CLASS", "confidence": 0.80, "bbox": [55, 10, 67, 30]},
        ],
        conf_threshold=0.50,
    )
    # FAKE_CLASS has char_type == "unknown", so it gets filtered out
    # With only 3 valid tokens remaining it's still displayable
    assert "UNKNOWN_CLASS" not in result.display_summary_ar


# ── C. Low confidence token is ignored ──

def test_low_confidence_token_ignored():
    """Tokens below threshold must not appear in the final plate text."""
    result = reconstruct_plate(
        [
            {"label": "1", "confidence": 0.90, "bbox": [10, 10, 20, 30]},
            {"label": "2", "confidence": 0.92, "bbox": [25, 10, 35, 30]},
            {"label": "alf", "confidence": 0.88, "bbox": [40, 10, 52, 30]},
            {"label": "ba2", "confidence": 0.10, "bbox": [55, 10, 67, 30]},  # too low
        ]
    )
    assert "ب" not in result.display_summary_ar


# ── D. Overlapping duplicates keep highest confidence ──

def test_overlapping_duplicate_keeps_highest_conf():
    """Two boxes at same position → keep the higher confidence one."""
    result = reconstruct_plate(
        [
            {"label": "6", "confidence": 0.85, "bbox": [19, 30, 31, 56]},
            {"label": "9", "confidence": 0.60, "bbox": [19, 30, 31, 56]},  # same box, lower conf
            {"label": "1", "confidence": 0.90, "bbox": [33, 29, 41, 55]},
            {"label": "alf", "confidence": 0.88, "bbox": [55, 30, 67, 55]},
        ]
    )
    # "6" wins over "9" because higher confidence at same position
    assert "٦" in result.digits_ar
    assert "٩" not in result.digits_ar


# ── E. Arabic mapping is correct for all letters ──

def test_arabic_mapping_completeness():
    """Each model class maps to the correct Arabic character."""
    from common.constants.plate_mapping import ARABIC_MAP

    expected = {
        "alf": "ا", "ba2": "ب", "gem": "ج", "dal": "د",
        "ra2": "ر", "sen": "س", "sad": "ص", "ta2": "ط",
        "ein": "ع", "fa2": "ف", "qaf": "ق", "lam": "ل",
        "mem": "م", "non": "ن", "ha2": "ه", "waw": "و",
        "ya2": "ي",
        "1": "١", "2": "٢", "3": "٣", "4": "٤", "5": "٥",
        "6": "٦", "7": "٧", "8": "٨", "9": "٩",
    }
    for key, value in expected.items():
        assert ARABIC_MAP[key] == value, f"ARABIC_MAP['{key}'] should be '{value}' but got '{ARABIC_MAP.get(key)}'"


# ── F. Final output does NOT auto-complete missing characters ──

def test_no_auto_completion_of_missing_chars():
    """If only 2 tokens survive, result should be 'unclear', not invented."""
    result = reconstruct_plate(
        [
            {"label": "1", "confidence": 0.90, "bbox": [10, 10, 20, 30]},
            {"label": "alf", "confidence": 0.88, "bbox": [40, 10, 52, 30]},
        ]
    )
    assert result.display_summary_ar == "اللوحة غير واضحة"
    assert result.token_count == 2


# ── G. One-row plate follows Egyptian convention ──

def test_one_row_egyptian_convention():
    """One-row plate: letters and digits are read right-to-left."""
    result = reconstruct_plate(
        [
            {"label": "7", "confidence": 0.87, "bbox": [6, 28, 18, 56]},
            {"label": "1", "confidence": 0.74, "bbox": [33, 29, 41, 55]},
            {"label": "3", "confidence": 0.79, "bbox": [46, 30, 56, 55]},
            {"label": "sad", "confidence": 0.87, "bbox": [64, 34, 82, 55]},
            {"label": "waw", "confidence": 0.69, "bbox": [84, 34, 98, 55]},
            {"label": "alf", "confidence": 0.64, "bbox": [103, 32, 111, 56]},
        ]
    )
    assert result.row_count == 1
    # Letters sorted right-to-left: alf(103) waw(84) sad(64)
    assert result.letters_ar == "اوص"
    # Digits sorted right-to-left: 3(46) 1(33) 7(6)
    assert result.digits_ar == "٣١٧"
    assert result.display_summary_ar == "اوص ٣١٧"


# ── H. Two-row plate follows Egyptian convention ──

def test_two_row_plate_convention():
    """Two-row plate: each row is read right-to-left independently."""
    result = reconstruct_plate(
        [
            {"label": "ha", "confidence": 0.90, "bbox": [10, 5, 20, 18]},
            {"label": "mem", "confidence": 0.91, "bbox": [25, 6, 38, 18]},
            {"label": "3", "confidence": 0.93, "bbox": [12, 28, 20, 42]},
            {"label": "4", "confidence": 0.92, "bbox": [24, 29, 32, 42]},
        ]
    )
    assert result.row_count == 2
    assert result.letters_ar == "مه"
    assert result.digits_ar == "٤٣"
    assert result.display_summary_ar == "مه ٤٣"


# ── I. Banner noise filtered out ──

def test_banner_noise_and_low_conf_filtered():
    """Full-width banners and very low confidence tokens are removed."""
    result = reconstruct_plate(
        [
            {"label": "4", "confidence": 0.03, "bbox": [0, 0, 120, 24]},   # banner noise
            {"label": "4", "confidence": 0.05, "bbox": [0, 0, 120, 28]},   # banner noise
            {"label": "7", "confidence": 0.87, "bbox": [6, 28, 18, 56]},
            {"label": "1", "confidence": 0.74, "bbox": [33, 29, 41, 55]},
            {"label": "3", "confidence": 0.79, "bbox": [46, 30, 56, 55]},
            {"label": "sad", "confidence": 0.87, "bbox": [64, 34, 82, 55]},
            {"label": "waw", "confidence": 0.69, "bbox": [84, 34, 98, 55]},
            {"label": "alf", "confidence": 0.64, "bbox": [103, 32, 111, 56]},
        ]
    )
    # The two banner "4" tokens are filtered out (low conf + oversized)
    assert result.row_count == 1
    assert result.plate_confidence > 0.6
    assert "٤" not in result.digits_ar


# ── Alias test: ha → ha2 normalization ──

def test_ha_alias_normalization():
    """Model class 'ha' should normalize to 'ha2' and map to 'ه'."""
    from common.utils.plate_reading import PlateToken

    token = PlateToken(raw_label="ha", confidence=0.9, x1=0, y1=0, x2=10, y2=10)
    assert token.normalized_label == "ha2"
    assert token.arabic_value == "ه"
    assert token.char_type == "letter"
