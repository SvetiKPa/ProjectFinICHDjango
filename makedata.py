import os
import django
import random
from datetime import timedelta, datetime

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from faker import Faker
from faker.providers import DynamicProvider
from django.contrib.auth.hashers import make_password
from django.utils import timezone
from django.db import transaction

from apps.booking.models import (
    User, Booking, Listing, Review, Address, Calendar,
    SearchHistory, ViewHistory
)
from apps.booking.enums import (
    Role, PropertyType, Status, BookingStatus
)

# Настройка Faker для немецких данных
faker = Faker('de_DE')

# Кастомные провайдеры для немецких данных
german_cities_provider = DynamicProvider(
    provider_name="german_city",
    elements=["Berlin", "München", "Hamburg", "Köln", "Frankfurt am Main",
              "Stuttgart", "Düsseldorf", "Dortmund", "Essen", "Leipzig",
              "Bremen", "Dresden", "Hannover", "Nürnberg", "Duisburg"]
)

german_states_provider = DynamicProvider(
    provider_name="german_state",
    elements=["Baden-Württemberg", "Bayern", "Berlin", "Brandenburg", "Bremen",
              "Hamburg", "Hessen", "Niedersachsen", "Nordrhein-Westfalen",
              "Rheinland-Pfalz", "Saarland", "Sachsen", "Sachsen-Anhalt",
              "Schleswig-Holstein", "Thüringen"]
)

faker.add_provider(german_cities_provider)
faker.add_provider(german_states_provider)


def create_german_users(count=20):
    """Создание немецких пользователей с ролями"""
    print("\n=== Создание пользователей ===")
    users = []

    # Создаем арендодателей (role=Role.LESSOR)
    for i in range(5):
        user = User.objects.create(
            username=f"lessor_{i + 1}",
            email=f"lessor{i + 1}@example.com",
            first_name=faker.first_name(),
            last_name=faker.last_name(),
            age=random.randint(30, 65),
            phone=f"+49{faker.msisdn()[:11]}",
            password=make_password("test123"),
            role=Role.LESSOR.value,
            is_active=True,
            created_at=timezone.now()
        )
        users.append(user)
        print(f"Арендодатель: {user.username} ({user.first_name} {user.last_name})")

    # Создаем арендаторов (role=Role.LESSEE)
    for i in range(count - 5):
        user = User.objects.create(
            username=f"lessee_{i + 1}",
            email=f"lessee{i + 1}@example.com",
            first_name=faker.first_name(),
            last_name=faker.last_name(),
            age=random.randint(20, 45),
            phone=f"+49{faker.msisdn()[:11]}",
            password=make_password("test123"),
            role=Role.LESSEE.value,
            is_active=True,
            created_at=timezone.now()
        )
        users.append(user)
        print(f"Арендатор: {user.username}")

    return users


def create_german_addresses(count=50):
    """Создание немецких адресов с учетом структуры модели"""
    print("\n=== Создание немецких адресов ===")
    addresses = []

    street_types = {
        "straße": "Str.",
        "weg": "Weg",
        "allee": "Allee",
        "platz": "Platz",
        "ring": "Ring",
        "ufer": "Ufer",
        "chaussee": "Ch."
    }

    # Районы для разных городов
    city_districts = {
        "Berlin": ["Mitte", "Kreuzberg", "Charlottenburg", "Prenzlauer Berg", "Friedrichshain",
                   "Neukölln", "Tempelhof", "Schöneberg", "Spandau", "Steglitz"],
        "München": ["Schwabing", "Maxvorstadt", "Haidhausen", "Giesing", "Neuhausen",
                    "Sendling", "Pasing", "Bogenhausen", "Berg am Laim", "Milbertshofen"],
        "Hamburg": ["St. Pauli", "Altona", "Eimsbüttel", "Winterhude", "Harburg",
                    "Bergedorf", "Wandsbek", "Billstedt", "Lurup", "Finkenwerder"],
        "Köln": ["Innenstadt", "Ehrenfeld", "Nippes", "Lindenthal", "Rodenkirchen",
                 "Porz", "Kalk", "Chorweiler", "Mülheim"],
        "Frankfurt am Main": ["Innenstadt", "Sachsenhausen", "Bornheim", "Bockenheim",
                              "Nordend", "Ostend", "Westend", "Gallus", "Griesheim"]
    }

    for i in range(count):
        city = faker.german_city()

        # Определяем район (district) - может быть пустым (blank=True)
        district = ""
        if city in city_districts and random.random() > 0.3:
            district = random.choice(city_districts[city])

        # Создаем полное название улицы с номером дома
        street_name = faker.street_name()
        street_type = random.choice(list(street_types.keys()))
        house_number = random.randint(1, 200)

        # Варианты формата адреса
        address_formats = [
            f"{street_name} {street_types[street_type]} {house_number}",
            f"{street_name} {house_number}",
            f"{street_name}{street_types[street_type]} {house_number}"
        ]

        full_address = random.choice(address_formats)

        # Генерация координат в зависимости от города
        if city == "Berlin":
            lat = random.uniform(52.45, 52.55)
            lon = random.uniform(13.28, 13.48)
        elif city == "München":
            lat = random.uniform(48.10, 48.18)
            lon = random.uniform(11.50, 11.65)
        elif city == "Hamburg":
            lat = random.uniform(53.50, 53.65)
            lon = random.uniform(9.90, 10.10)
        elif city == "Köln":
            lat = random.uniform(50.90, 51.00)
            lon = random.uniform(6.90, 7.05)
        else:
            lat = random.uniform(47.0, 55.0)
            lon = random.uniform(6.0, 15.0)

        address = Address.objects.create(
            address=full_address,  # "Улица и номер дома"
            city=city,
            district=district,  # Может быть пустым
            state=faker.german_state(),
            country="Германия",  # По умолчанию в модели
            postal_code=faker.postcode(),
            latitude=round(lat, 6),
            longitude=round(lon, 6)
        )

        addresses.append(address)
        district_info = f" ({district})" if district else ""
        print(f"Адрес {i + 1}: {address.city}{district_info}, {address.address}")

    return addresses


def create_german_listings(users, addresses, count=100):
    """Создание немецких объявлений"""
    print("\n=== Создание немецких объявлений ===")
    listings = []

    # Берем пользователей с ролью LESSOR как арендодателей
    lessors = [u for u in users if u.role == Role.LESSOR.value]

    # Немецкие описания
    descriptions_de = [
        "Schöne, helle Wohnung in ruhiger Lage mit guter Anbindung an öffentliche Verkehrsmittel.",
        "Moderne Einrichtung, voll ausgestattete Küche mit Terrasse und Blick auf den Garten.",
        "Zentrale Lage, in der Nähe von U-Bahn-Stationen, Supermärkten und Restaurants.",
        "Nettes Appartement mit Blick auf den Park, ideal für Paare oder Geschäftsreisende.",
        "Geräumiges Haus mit großem Garten und Spielplatz, perfekt für Familien mit Kindern.",
        "Neuwertige Ausstattung mit Fußbodenheizung, Balkon und Einbauküche von Siemens.",
        "Altbauwohnung mit hohen Decken, Stuck und originalen Holzböden aus den 1920er Jahren.",
        "Neubauwohnung mit Energieeffizienzklasse A++, Tiefgaragenstellplatz und Aufzug verfügbar.",
        "Gemütliche Dachgeschosswohnung mit tollem Ausblick über die Stadt, voll möbliert.",
        "Wohnung in historischem Gebäude unter Denkmalschutz, vor 2 Jahren komplett renoviert.",
        "Helle 3-Zimmer-Wohnung mit Einbauküche, Bad mit Fenster und separatem WC.",
        "Ruhige Lage am Stadtrand, aber mit guter Anbindung ins Zentrum (20 Minuten mit der S-Bahn).",
        "Wohnung mit Südbalkon, Einbauschrank in jedem Zimmer und neuer Gasheizung.",
        "Erstbezug nach Sanierung, bodentiefe Fenster, Parkettböden und elektrische Rollläden.",
        "Barrierefreie Wohnung im Erdgeschoss mit ebenerdiger Dusche und breiten Türen."
    ]

    # Немецкие заголовки
    titles_de = [
        "Helle und moderne {type} in {city}",
        "Gemütliche {type} in ruhiger {city}-Lage",
        "Zentral gelegene {type} in {city}",
        "Neuwertige {type} mit Balkon in {city}",
        "Großzügige {type} для Familien in {city}"
    ]

    # Получаем все доступные типы недвижимости из enum
    property_types = [pt.value for pt in PropertyType]

    # Немецкие названия типов
    property_type_german = {
        "apartment": "Wohnung",
        "house": "Haus",
        "hotel": "Hotel",
        "hostel": "Hostel",
        "studio": "Studio",
        "villa": "Villa",
        "cottage": "Cottage",
        "townhouse": "Townhouse",
        "penthouse": "Penthouse",
        "duplex": "Duplex",
        "loft": "Loft"
    }

    for i in range(count):
        # Выбираем случайные данные
        lessor = random.choice(lessors)
        address = random.choice(addresses)
        property_type = random.choice(property_types)

        # Генерация цены в зависимости от города и типа
        if address.city in ["München", "Frankfurt am Main", "Hamburg"]:
            base_price = random.randint(100, 350)
        elif address.city in ["Berlin", "Köln", "Stuttgart", "Düsseldorf"]:
            base_price = random.randint(90, 250)
        else:
            base_price = random.randint(30, 180)

        # Корректировка цены по типу жилья
        if property_type in [PropertyType.HOUSE.value, PropertyType.VILLA.value,
                             PropertyType.PENTHOUSE.value, PropertyType.COTTAGE.value]:
            base_price = int(base_price * 1.8)
        elif property_type == PropertyType.APARTMENT.value:
            base_price = int(base_price * 1.2)
        elif property_type == PropertyType.STUDIO.value:
            base_price = int(base_price * 0.8)

        # Выбираем статус из enum
        status_choices = [Status.DRAFT.value, Status.PUBLISHED.value,
                          Status.ARCHIVED.value, Status.RENTED.value]
        status_weights = [0.1, 0.6, 0.1, 0.2]

        # Создаем заголовок
        title_template = random.choice(titles_de)
        title = title_template.format(
            type=property_type_german.get(property_type, property_type),
            city=address.city
        )

        # Добавляем район если есть
        if address.district:
            title += f" ({address.district})"

        listing = Listing.objects.create(
            title=title,
            description=random.choice(descriptions_de),
            address=address,
            lessor=lessor,
            price=base_price,
            deposit=round(base_price * 3) if random.random() > 0.3 else None,
            property_type=property_type,
            rooms=random.randint(1, 5),
            bedrooms=random.randint(1, 3),
            bathrooms=random.randint(1, 2),
            area_sqm=round(random.uniform(35, 150), 1),
            has_kitchen=True if random.random() > 0.1 else False,
            has_balcony=random.choice([True, False]),
            has_parking=random.choice([True, False]),
            has_elevator=random.choice([True, False]),
            has_furniture=random.choice([True, False]),
            has_internet=True,
            pets_allowed=random.choice([True, False]),
            smoking_allowed=False if random.random() > 0.8 else True,
            max_guests=random.randint(1, 6),
            min_stay_days=random.randint(1, 3),
            max_stay_days=random.randint(90, 365),
            available_from=timezone.now().date() + timedelta(days=random.randint(0, 7)),
            available_until=timezone.now().date() + timedelta(days=random.randint(180, 365)),
            is_available=random.choice([True, False]),
            is_featured=True if random.random() > 0.7 else False,
            status=random.choices(status_choices, weights=status_weights)[0],
            published_at=timezone.now() if random.random() > 0.3 else None
        )

        listings.append(listing)
        print(f"Объявление {i + 1}: {listing.title} - {listing.price}€/Monat - {listing.rooms} Zimmer")

    return listings


from decimal import Decimal


def create_fixed_bookings(users, listings, count=80):
    """Создание бронирований с исправленными ценами"""
    bookings = []

    tenants = [u for u in users if u.role == Role.LESSEE.value]
    published_listings = [l for l in listings if l.status == Status.PUBLISHED.value]

    for i in range(min(count, len(published_listings) * 3)):
        listing = random.choice(published_listings)
        tenant = random.choice(tenants)

        booking_code = f"DE{datetime.now().year}{random.randint(1000, 9999)}"

        # Даты
        check_in_date = timezone.now().date() + timedelta(days=random.randint(1, 60))
        stay_days = random.randint(2, min(14, listing.max_stay_days or 14))
        check_out_date = check_in_date + timedelta(days=stay_days)

        # Цены с округлением до 2 знаков
        daily_price = Decimal(str(listing.price)) / Decimal('30')
        base_price = round(daily_price * Decimal(str(stay_days)), 2)
        total_amount = base_price

        # Статус
        status = random.choice([
            BookingStatus.PENDING.value,
            BookingStatus.CONFIRMED.value,
            BookingStatus.CANCELLED.value
        ])

        try:
            booking = Booking.objects.create(
                listing=listing,
                lessee=tenant,
                check_in_date=check_in_date,
                check_out_date=check_out_date,
                number_of_guests=random.randint(1, 3),
                price=base_price,
                total_nights=stay_days,
                total_amount=total_amount,
                guest_first_name=tenant.first_name[:50],
                guest_last_name=tenant.last_name[:50],
                guest_email=tenant.email,
                status=status,
                booking_code=booking_code,
                is_paid=status == BookingStatus.CONFIRMED.value,
            )

            bookings.append(booking)
            print(f"✅ Бронирование {i + 1}: {booking_code} - {stay_days} дней")

        except Exception as e:
            print(f"❌ Пропущено: {e}")
            continue

    return bookings


def create_german_reviews(users, listings, bookings, count=30):
    """Создание немецких отзывов"""
    print("\n=== Создание немецких отзывов ===")
    reviews = []

    # Только завершенные бронирования
    completed_bookings = [b for b in bookings if b.status == BookingStatus.COMPLETED.value]

    if not completed_bookings:
        print("⚠️ Нет завершенных бронирований для создания отзывов")
        return reviews

    for i in range(min(count, len(completed_bookings))):
        booking = completed_bookings[i]

        try:
            review = Review.objects.create(
                listing=booking.listing,
                booking=booking,
                reviewer=booking.lessee,
                rating=round(random.uniform(7.0, 10.0), 1),
                comment=f"Отзыв на бронирование {booking.booking_code}. Отличное жилье в {booking.listing.address.city}!",
                created_at=booking.check_out_date + timedelta(days=random.randint(1, 14))
            )

            reviews.append(review)
            print(f"✅ Отзыв {i + 1} создан: {review.rating}/10 - {booking.booking_code}")

        except Exception as e:
            print(f"❌ Ошибка при создании отзыва: {e}")
            continue

    return reviews


def create_calendar_entries_for_listings(listings, bookings):
    """Создание записей в календаре для всех объявлений"""
    print("\n=== Создание записей календаря ===")

    total_entries = 0

    for listing in listings:
        print(f"Создание календаря для объявления: {listing.title}")

        # Создаем записи на 180 дней вперед от сегодня
        start_date = timezone.now().date()
        end_date = start_date + timedelta(days=180)

        current_date = start_date
        while current_date < end_date:
            # Проверяем, есть ли активное бронирование на эту дату
            is_booked = False
            related_booking = None

            # Ищем бронирования для этого объявления на эту дату
            for booking in bookings:
                if (booking.listing == listing and
                        booking.check_in_date <= current_date < booking.check_out_date and
                        booking.status in [BookingStatus.CONFIRMED.value,
                                           BookingStatus.COMPLETED.value,
                                           BookingStatus.ACTIVE.value]):
                    is_booked = True
                    related_booking = booking
                    break

            # Создаем запись в календаре
            try:
                Calendar.objects.create(
                    listing=listing,
                    target_date=current_date,
                    is_available=not is_booked,  # Если есть бронь - недоступно
                    booking=related_booking
                )
                total_entries += 1
            except Exception as e:
                # Если запись уже существует (уникальность по listing+date)
                print(f"  Запись на {current_date} уже существует: {e}")

            current_date += timedelta(days=1)

        print(f"  Создано записей календаря для объявления {listing.id}")

    print(f"\nВсего создано записей календаря: {total_entries}")


def create_calendar_entries_smart(listings, bookings, days_range=180):
    """Умное создание записей календаря с учетом логики бронирований"""
    print("\n=== Умное создание записей календаря ===")

    total_entries = 0

    for listing in listings:
        print(f"Календарь для: {listing.title[:40]}...")

        # Создаем записи на заданный диапазон дней
        start_date = timezone.now().date()
        end_date = start_date + timedelta(days=days_range)

        # Собираем все бронирования для этого объявления
        listing_bookings = [b for b in bookings if b.listing == listing]

        current_date = start_date
        dates_created = 0

        while current_date < end_date:
            # Проверяем доступность для этой даты
            is_available = True
            related_booking = None

            # Проверяем активные бронирования на эту дату
            for booking in listing_bookings:
                if (booking.check_in_date <= current_date < booking.check_out_date and
                        booking.status in [BookingStatus.CONFIRMED.value,
                                           BookingStatus.ACTIVE.value,
                                           BookingStatus.COMPLETED.value]):
                    is_available = False
                    related_booking = booking
                    break

            # Пропускаем даты, которые уже прошли (для истории)
            if current_date < timezone.now().date():
                # Для прошедших дат - случайная доступность
                is_available = random.random() > 0.7

            # Создаем запись
            try:
                Calendar.objects.update_or_create(
                    listing=listing,
                    target_date=current_date,
                    defaults={
                        'is_available': is_available,
                        'booking': related_booking
                    }
                )
                dates_created += 1
                total_entries += 1
            except Exception as e:
                print(f"  Ошибка для даты {current_date}: {e}")

            current_date += timedelta(days=1)

        print(f"  Создано {dates_created} записей")

    print(f"\n✅ Всего создано записей календаря: {total_entries}")
    return total_entries


def create_search_history(users, count=50):
    """Создание истории поиска"""
    print("\n=== Создание истории поиска ===")

    for i in range(count):
        user = random.choice(users)

        # Базовые фильтры
        filters = {
            'city': random.choice(["Berlin", "München", "Hamburg"]),
            'min_price': random.randint(300, 800),
            'max_price': random.randint(1200, 3000),
            'rooms': random.randint(1, 3),
        }

        # Опциональные фильтры
        if random.random() > 0.5:
            filters['property_type'] = random.choice(['apartment', 'house', 'studio'])

        if random.random() > 0.3:
            filters['has_balcony'] = True

        SearchHistory.objects.create(
            user=user,
            query=random.choice(["Wohnung", "Apartment", "Haus", "Studio"]),
            filters=filters,
            results_count=random.randint(10, 100),
            created_at=timezone.now() - timedelta(days=random.randint(1, 90))
        )

    print(f"Создано записей истории поиска: {count}")

def create_view_history(users, listings, count=100):
    """Создание истории просмотров"""
    print("\n=== Создание истории просмотров ===")

    for i in range(count):
        user = random.choice(users)
        listing = random.choice(listings)

        ViewHistory.objects.create(
            user=user if random.random() > 0.3 else None,  # 30% анонимных просмотров
            listing=listing,
            ip_address=faker.ipv4(),
            user_agent=random.choice([
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15",
                "Mozilla/5.0 (iPhone; CPU iPhone OS 17_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1",
                "Mozilla/5.0 (Linux; Android 13; SM-S901B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.6099.210 Mobile Safari/537.36"
            ]),
            created_at=timezone.now() - timedelta(days=random.randint(0, 90))
        )

    print(f"Создано записей истории просмотров: {count}")


def verify_calendar_data():
    """Проверка данных календаря"""
    print("\n=== Проверка данных календаря ===")

    total_calendar = Calendar.objects.count()
    print(f"Всего записей в календаре: {total_calendar}")

    available = Calendar.objects.filter(is_available=True).count()
    booked = Calendar.objects.filter(is_available=False).count()

    print(f"Свободных дат: {available} ({available / total_calendar * 100:.1f}%)")
    print(f"Занятых дат: {booked} ({booked / total_calendar * 100:.1f}%)")

    # Проверка уникальности (listing + date)
    from django.db.models import Count
    duplicates = Calendar.objects.values('listing', 'target_date') \
        .annotate(count=Count('id')) \
        .filter(count__gt=1)

    if duplicates.exists():
        print(f"⚠️ Найдено дубликатов: {duplicates.count()}")
    else:
        print("✅ Дубликатов не найдено")

    # Примеры записей
    print("\nПримеры записей календаря:")
    sample_calendars = Calendar.objects.select_related('listing', 'booking')[:5]
    for cal in sample_calendars:
        status = "СВОБОДНО" if cal.is_available else "ЗАНЯТО"
        booking_info = f" (Бронирование: {cal.booking.booking_code})" if cal.booking else ""
        print(f"  {cal.target_date}: {status} - {cal.listing.title[:30]}...{booking_info}")


@transaction.atomic
def main():
    """Основная функция для наполнения базы"""
    print("=" * 60)
    print("НАПОЛНЕНИЕ БАЗЫ ДАННЫХ - НОВАЯ СТРУКТУРА CALENDAR")
    print("=" * 60)

    # Очистка старых данных (опционально)
    clear_old = input("Очистить старые данные? (y/n): ").lower() == 'y'

    if clear_old:
        print("\n🧹 Очистка старых данных...")
        Calendar.objects.all().delete()
        Review.objects.all().delete()
        Booking.objects.all().delete()
        ViewHistory.objects.all().delete()
        SearchHistory.objects.all().delete()
        Listing.objects.all().delete()
        Address.objects.all().delete()
        User.objects.exclude(is_superuser=True).delete()
        print("✅ Очистка завершена!\n")

    # Создание данных
    print("🚀 Начало создания данных...")

    users = create_german_users(20)
    addresses = create_german_addresses(60)
    listings = create_german_listings(users, addresses, 100)
    bookings = create_fixed_bookings(users, listings, 200)
    reviews = create_german_reviews(users, listings, bookings, 40)

    # Создание календаря (самая важная часть)
    create_calendar_entries_smart(listings, bookings, days_range=90)

    # Опционально: история поиска и просмотров
    create_search_history(users, 30)
    create_view_history(users, listings, 50)

    print("\n" + "=" * 60)
    print("✅ НАПОЛНЕНИЕ ЗАВЕРШЕНО!")
    print("=" * 60)

    # Подробная статистика
    print(f"\n📊 СТАТИСТИКА:")
    print(f"├─ 👤 Пользователей: {User.objects.count()}")
    print(f"│  ├─ Арендодателей: {User.objects.filter(role=Role.LESSOR.value).count()}")
    print(f"│  └─ Арендаторов: {User.objects.filter(role=Role.LESSEE.value).count()}")

    print(f"├─ 🏠 Адресов: {Address.objects.count()}")

    print(f"├─ 🏢 Объявлений: {Listing.objects.count()}")
    for status in Status:
        count = Listing.objects.filter(status=status.value).count()
        if count > 0:
            print(f"│  ├─ {status.value}: {count}")

    print(f"├─ 📅 Бронирований: {Booking.objects.count()}")
    for status in BookingStatus:
        count = Booking.objects.filter(status=status.value).count()
        if count > 0:
            print(f"│  ├─ {status.value}: {count}")

    print(f"├─ ⭐ Отзывов: {Review.objects.count()}")

    # Проверка календаря
    verify_calendar_data()

    print("\n" + "=" * 60)
    print("🎯 ТЕСТОВЫЕ УЧЕТНЫЕ ЗАПИСИ:")
    print("=" * 60)

    # Примеры тестовых данных
    print("\n1. АРЕНДОДАТЕЛИ (могут создавать объявления):")
    lessors = User.objects.filter(role=Role.LESSOR.value)[:2]
    for lessor in lessors:
        listing_count = Listing.objects.filter(lessor=lessor).count()
        print(f"   👤 {lessor.username} ({lessor.email})")
        print(f"      Пароль: test123 | Объявлений: {listing_count}")

    print("\n2. АРЕНДАТОРЫ (могут бронировать):")
    tenants = User.objects.filter(role=Role.LESSEE.value)[:2]
    for tenant in tenants:
        booking_count = Booking.objects.filter(lessee=tenant).count()
        print(f"   👤 {tenant.username} ({tenant.email})")
        print(f"      Пароль: test123 | Бронирований: {booking_count}")

    print("\n3. ПРИМЕРЫ БРОНИРОВАНИЙ С КАЛЕНДАРЕМ:")
    active_bookings = Booking.objects.filter(
        status__in=[BookingStatus.CONFIRMED.value, BookingStatus.ACTIVE.value]
    )[:3]

    for booking in active_bookings:
        # Находим записи календаря для этого бронирования
        calendar_dates = Calendar.objects.filter(
            booking=booking,
            target_date__range=[booking.check_in_date, booking.check_out_date - timedelta(days=1)]
        )

        print(f"   📅 Бронирование {booking.booking_code}:")
        print(f"      {booking.check_in_date} - {booking.check_out_date}")
        print(f"      Заблокировано дней: {calendar_dates.count()}")
        print(f"      Объявление: {booking.listing.title[:40]}...")

    print("\n4. ПРОВЕРКА ДОСТУПНОСТИ:")
    sample_listing = Listing.objects.filter(status=Status.PUBLISHED.value).first()
    if sample_listing:
        print(f"   📆 Доступность для {sample_listing.title[:30]}...")

        # Проверяем следующие 7 дней
        for i in range(7):
            check_date = timezone.now().date() + timedelta(days=i)
            try:
                calendar_entry = Calendar.objects.get(
                    listing=sample_listing,
                    target_date=check_date
                )
                status = "✅ СВОБОДНО" if calendar_entry.is_available else "❌ ЗАНЯТО"
                booking_info = f" ({calendar_entry.booking.booking_code})" if calendar_entry.booking else ""
                print(f"      {check_date}: {status}{booking_info}")
            except Calendar.DoesNotExist:
                print(f"      {check_date}: ❓ НЕТ ДАННЫХ")


if __name__ == "__main__":
    main()