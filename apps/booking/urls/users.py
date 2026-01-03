from django.urls import path
from apps.booking.views.users import (
    RegisterUser,
    UserLoginAPIView,
    UserListView,
    LogOutUser)

urlpatterns = [
    path('register/', RegisterUser.as_view(), name='register'),
    path('login/', UserLoginAPIView.as_view(), name='login'),
    path('logout/', LogOutUser.as_view(), name='logout'),
    path('', UserListView.as_view()),
]