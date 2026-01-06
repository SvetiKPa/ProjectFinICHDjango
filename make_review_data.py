import os
import django
import random
from datetime import timedelta, datetime

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

# from faker import Faker
from apps.booking.models import User, Booking, Listing, Review
from apps.booking.enums import BookingStatus
#
# # Настройка Faker для немецких данных
# faker = Faker('de_DE')


def create_reviews_for_completed_bookings():
    """Создание отзывов для завершенных бронирований"""
    print("\n=== Создание отзывов для завершенных бронирований ===")
    completed_bookings = Booking.objects.filter(
        status=BookingStatus.COMPLETED.value,
        is_deleted=False
    ).select_related('listing', 'lessee')

    print(f"Найдено завершенных бронирований: {completed_bookings.count()}")

    reviews_created = 0

    for booking in completed_bookings:
        if hasattr(booking, 'review'):
            continue
        if not booking.lessee:
            continue

        # Генерируем рейтинг (от 3 до 5 звезд, с распределением)
        rating = random.choices(
            [3.0, 3.5, 4.0, 4.5, 5.0],
            weights=[0.05, 0.1, 0.2, 0.3, 0.35]
        )[0]
        german_reviews = [
            f"Sehr schöne Unterkunft in {booking.listing.address.city}. Alles war sauber und ordentlich. Gerne wieder!",
            f"Tolle Lage, gute Verkehrsanbindung. Die Wohnung war genau wie beschrieben. Sehr netter Vermieter.",
            f"Alles perfekt! Check-in war unkompliziert, die Wohnung ist gemütlich eingerichtet. Sehr zu empfehlen.",
            f"Schöne, helle Wohnung mit allem, was man braucht. Supermarkt und Restaurants in der Nähe.",
            f"Sehr zufrieden mit dem Aufenthalt. Kommunikation mit dem Vermieter war ausgezeichnet.",
            f"Moderne Einrichtung, alles funktioniert einwandfrei. Besonders der Balkon war toll.",
            f"Perfekt für unseren Städtetrip. Zentrale Lage, zu Fuß gut zu erreichen.",
            f"Sehr sauber und gepflegt. Die Küche ist voll ausgestattet. Würde wieder buchen.",
            f"Ruhige Lage trotz Zentrumsnähe. Gute Betten, bequeme Matratzen. Alles bestens.",
            f"Toller Aufenthalt! Die Bilder entsprechen der Realität. Sehr freundlicher Empfang.",
        ]
        try:
            review = Review.objects.create(
                listing=booking.listing,
                booking=booking,
                reviewer=booking.lessee,
                rating=rating,
                comment=random.choice(german_reviews),
                created_at=booking.check_out_date + timedelta(days=random.randint(1, 7))
            )
            reviews_created += 1
            print(f"✅ Создан отзыв {reviews_created}: {rating}/5 - {booking.booking_code}")
        except Exception as e:
            print(f" Ошибка при создании отзыва для бронирования {booking.id}: {e}")
            continue
    return reviews_created


def main():
    reviews_created = create_reviews_for_completed_bookings()


if __name__ == "__main__":
    main()
