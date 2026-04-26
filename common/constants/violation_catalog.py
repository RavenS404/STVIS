from common.constants.enums import ViolationCode


VIOLATION_CATALOG = {
    "un seat-belt": {
        "code": ViolationCode.UNFASTENED_SEAT_BELT.value,
        "name_ar": "عدم ربط حزام الأمان",
        "name_en": "Unfastened seat belt",
        "actionable": True,
    },
    "using_mobile": {
        "code": ViolationCode.USING_MOBILE.value,
        "name_ar": "استخدام الهاتف أثناء القيادة",
        "name_en": "Using mobile phone while driving",
        "actionable": True,
    },
    "wrong_way": {
        "code": ViolationCode.WRONG_WAY.value,
        "name_ar": "السير عكس الاتجاه",
        "name_en": "Wrong-way driving",
        "actionable": True,
    },
    "seat-belt": {
        "code": "seat_belt_present",
        "name_ar": "حزام الأمان ظاهر",
        "name_en": "Seat belt detected",
        "actionable": False,
    },
}

VEHICLE_ANCHOR_LABELS = {"vehicle", "car windshield"}
PLATE_BOX_LABEL = "car_plate"
