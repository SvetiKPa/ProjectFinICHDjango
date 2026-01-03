from enum import  StrEnum, IntEnum


class Role(StrEnum):
    LESSOR = "lessor"
    LESSEE = "lessee"

    @classmethod
    def choices(cls):
        human_readable = {
            cls.LESSOR: "Арендодатель",
            cls.LESSEE: "Арендатор",
        }
        return [(item.value, human_readable[item]) for item in cls]

class AvailabilityStatus(IntEnum):
    FREE = 0  # Свободно
    BUSY = 1  # Занято

    @classmethod
    def choices(cls):
        human_readable = {
            cls.FREE: "Свободно",
            cls.BUSY: "Занято",
        }
        return [(item.value, human_readable[item]) for item in cls]

class TimeSlot(IntEnum):
    """Временные слоты дня"""
    WHOLE_DAY = 0  # Весь день
    MORNING = 1  # Утро (9:00-14:00)
    AFTERNOON = 2  # День/Вечер (14:00-21:00)

    @classmethod
    def choices(cls):
        human_readable = {
            cls.WHOLE_DAY: "Весь день",
            cls.MORNING: "Утро (до 14:00)",
            cls.AFTERNOON: "День/Вечер (после 14:00)",
        }
        return [(item.value, human_readable[item]) for item in cls]

class PropertyType(StrEnum):
    APARTMENT = "apartment"
    HOUSE = "house"
    HOTEL = "hotel"
    HOSTEL = "hostel"
    STUDIO = "studio"
    VILLA = "villa"
    COTTAGE = "cottage"
    TOWNHOUSE = "townhouse"
    PENTHOUSE = "penthouse"
    DUPLEX = "duplex"
    LOFT = "loft"

    @classmethod
    def choices(cls):
        human_readable = {
            cls.APARTMENT: "Квартира",
            cls.HOUSE: "Дом",
            cls.HOTEL: "Отель",
            cls.HOSTEL: "Хостел",
            cls.STUDIO: "Студия",
            cls.VILLA: "Вилла",
            cls.COTTAGE: "Коттедж",
            cls.TOWNHOUSE: "Таунхаус",
            cls.PENTHOUSE: "Пентхаус",
            cls.DUPLEX: "Дуплекс",
            cls.LOFT: "Лофт",
        }
        return [(item.value, human_readable[item]) for item in cls]

class Status(StrEnum):
    DRAFT = "draft"
    PUBLISHED = "published"
    ARCHIVED = "archived"
    RENTED = "rented"

    @classmethod
    def choices(cls):
        human_readable = {
            cls.DRAFT: "Черновик",
            cls.PUBLISHED: "Опубликовано",
            cls.ARCHIVED: "В архиве",
            cls.RENTED: "Сдано",
        }
        return [(item.value, human_readable[item]) for item in cls]

class BookingStatus(StrEnum):
    PENDING = 'pending'
    CONFIRMED = 'confirmed'
    CANCELLED = 'cancelled'
    COMPLETED = 'completed'
    REJECTED = 'rejected'

    @classmethod
    def choices(cls):
        human_readable = {
            cls.PENDING: 'ожидает подтверждения',
            cls.CONFIRMED : 'confirmed',
            cls.CANCELLED : 'cancelled',
            cls.COMPLETED : 'completed',
            cls.REJECTED : 'rejected',
        }
        return [(item.value, human_readable[item]) for item in cls]
