from django.urls import path
from .views import (
    GroupListView, GroupCreateView, GroupUpdateView, GroupDeleteView,
    MarkNotificationReadView
)

urlpatterns = [
    # Grupos
    path('groups/', GroupListView.as_view(), name='notification_group_list'),
    path('groups/add/', GroupCreateView.as_view(), name='notification_group_create'),
    path('groups/<int:pk>/edit/', GroupUpdateView.as_view(), name='notification_group_edit'),
    path('groups/<int:pk>/delete/', GroupDeleteView.as_view(), name='notification_group_delete'),

    # Notificaciones
    path('read/<int:pk>/', MarkNotificationReadView.as_view(), name='mark_notification_read'),
]
