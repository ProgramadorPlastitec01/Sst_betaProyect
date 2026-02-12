from django.urls import path
from . import views

urlpatterns = [
    # Listado de roles
    path('', views.RoleListView.as_view(), name='role_list'),
    
    # CRUD de roles
    path('create/', views.RoleCreateView.as_view(), name='role_create'),
    path('<int:pk>/', views.RoleDetailView.as_view(), name='role_detail'),
    path('<int:pk>/edit/', views.RoleUpdateView.as_view(), name='role_edit'),
    path('<int:pk>/delete/', views.RoleDeleteView.as_view(), name='role_delete'),
    
    # Gestión de permisos
    path('<int:pk>/permissions/', views.role_permissions_view, name='role_permissions'),
    
    # Activar/Desactivar rol
    path('<int:pk>/toggle/', views.toggle_role_status, name='role_toggle'),
]
