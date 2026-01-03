from django.urls import path, include
from rest_framework.routers import DefaultRouter, SimpleRouter
from apps.booking.views.reviews import ReviewListCreateView, ReviewDetailView, my_reviews

# router = SimpleRouter()
# router = DefaultRouter()
# router.register('', ReviewViewSet)  #viewset

# urlpatterns = [
#     path('', include(router.urls)),
#     # Дополнительные endpoints
#     path('listing/<int:listing_id>/', ReviewViewSet.as_view({'get': 'listing_reviews'}), name='listing-reviews'),
# ]
urlpatterns = [
    path('', ReviewListCreateView.as_view()),  # GET, POST
    path('<int:pk>/', ReviewDetailView.as_view()),  # GET, PUT, PATCH, DELETE
    path('my_reviews/', my_reviews),  # GET
    # listing/<id>/ уже работает через ?listing=id в основном эндпоинте
]