from django.contrib import admin
from .models import Permission, Role


@admin.register(Permission)
class PermissionAdmin(admin.ModelAdmin):
    list_display = ['module', 'action', 'codename', 'is_active']
    list_filter = ['module', 'action', 'is_active']
    search_fields = ['codename', 'description']
    ordering = ['module', 'action']


@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ['name', 'is_active', 'is_system_role', 'permission_count', 'user_count']
    list_filter = ['is_active', 'is_system_role']
    search_fields = ['name', 'description']
    filter_horizontal = ['permissions']
    
    def permission_count(self, obj):
        return obj.permissions.count()
    permission_count.short_description = 'Permisos'
    
    def user_count(self, obj):
        return obj.users.count()
    user_count.short_description = 'Usuarios'
