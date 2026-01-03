from django.contrib import admin, messages
from .models import Listing, Address, Booking


# from apps.booking.models import Listing

# class AddressInline(admin.TabularInline):
#     model = Address
#     extra = 1  # Количество пустых форм для подзадач
    # fields = ['city', 'address', 'country']
    # list_display = ['country']


@admin.register(Listing)
class ListingAdmin(admin.ModelAdmin):
    list_display = ['title', 'display_city', 'price', 'lessor']

    def display_city(self, obj):
        return obj.address.city if obj.address else "-"

    display_city.short_description = "Город"

@admin.register(Address)
class AddressAdmin(admin.ModelAdmin):
    list_display = ['city', 'address', 'country', 'latitude', 'longitude']

@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ['check_in_date',
                    'check_out_date',
                    'booking_code',
                    'guest_first_name',
                    'guest_last_name',
                    ]

