from django.urls import path, include
from rest_framework.routers import DefaultRouter, SimpleRouter
from apps.booking.views.reviews import ReviewViewSet

# router = SimpleRouter()
router = DefaultRouter()
router.register('', ReviewViewSet)  #viewset

urlpatterns = [
    path('', include(router.urls)),
    # Дополнительные endpoints
    # path('listing/<int:listing_id>/', ReviewViewSet.as_view({'get': 'listing_reviews'}), name='listing-reviews'),
]
# GET    /api/v1/reviews/           - список всех отзывов
# POST   /api/v1/reviews/           - создать отзыв
# GET    /api/v1/reviews/{id}/      - получить отзыв по ID
# PUT    /api/v1/reviews/{id}/      - полное обновление отзыва
# PATCH  /api/v1/reviews/{id}/      - частичное обновление отзыва
# DELETE /api/v1/reviews/{id}/      - удалить отзыв
# GET    /api/v1/reviews/my/        - мои отзывы (кастомный action)