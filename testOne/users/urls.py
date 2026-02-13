from django.urls import path
from django.contrib.auth.views import LogoutView
from .views import (
    CustomLoginView, DashboardView, UserListView, 
    UserCreateView, UserUpdateView, UserDeleteView,
    ProfileView, UserPasswordChangeView, DigitalSignatureUpdateView
)

urlpatterns = [
    path('login/', CustomLoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(next_page='login'), name='logout'),
    path('dashboard/', DashboardView.as_view(), name='dashboard'),
    path('users/', UserListView.as_view(), name='user_list'),
    path('users/create/', UserCreateView.as_view(), name='user_create'),
    path('users/<int:pk>/edit/', UserUpdateView.as_view(), name='user_edit'),
    path('users/<int:pk>/delete/', UserDeleteView.as_view(), name='user_delete'),
    path('profile/', ProfileView.as_view(), name='user_profile'),
    path('profile/password/', UserPasswordChangeView.as_view(), name='user_password_change'),
    path('profile/signature/', DigitalSignatureUpdateView.as_view(), name='update_signature'),
]
