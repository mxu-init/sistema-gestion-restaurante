from enum import Enum


class ReservationStatus(str, Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    SEATED = "seated"
    CANCELLED = "cancelled"
    NO_SHOW = "no_show"


class ReservationOrigin(str, Enum):
    PHONE = "phone"
    IN_PERSON = "in_person"
