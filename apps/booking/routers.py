from django.urls import path, include
from rest_framework.response import Response
from rest_framework.decorators import api_view
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

@api_view(['GET'])
def api_root(request):
    return Response({'message': 'API v1 работает!'})


urlpatterns = [
    path('', api_root),
    path('users/', include('apps.booking.urls.users')),
    path('listings/', include('apps.booking.urls.listings')),
    path('bookings/', include('apps.booking.urls.bookings')),
    path('reviews/', include('apps.booking.urls.reviews')),
    path('calendars/', include('apps.booking.urls.calendars')),

    # JWT аутентификация
    path('jwt-auth/', TokenObtainPairView.as_view()),
    path('jwt-refresh/', TokenRefreshView.as_view()),

]
