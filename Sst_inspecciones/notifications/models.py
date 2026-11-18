from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _

class NotificationGroup(models.Model):
    name = models.CharField(max_length=100, unique=True, verbose_name="Nombre del Grupo")
    description = models.TextField(blank=True, verbose_name="Descripción")
    users = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='notification_groups', blank=True, verbose_name="Usuarios")
    is_active = models.BooleanField(default=True, verbose_name="Activo")
    is_system_default = models.BooleanField(default=False, editable=False, verbose_name="Por defecto del sistema")

    class Meta:
        verbose_name = "Grupo de Notificación"
        verbose_name_plural = "Grupos de Notificación"
    
    def __str__(self):
        return self.name

class Notification(models.Model):
    TYPE_CHOICES = [
        ('system', 'Sistema'),
        ('alert', 'Alerta'),
        ('inspection', 'Inspección'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='notifications', verbose_name="Usuario")
    title = models.CharField(max_length=200, verbose_name="Título")
    message = models.TextField(verbose_name="Mensaje")
    link = models.CharField(max_length=255, blank=True, null=True, verbose_name="Enlace de Acción")
    notification_type = models.CharField(max_length=20, choices=TYPE_CHOICES, default='system', verbose_name="Tipo")
    is_read = models.BooleanField(default=False, verbose_name="Leída")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de Creación")

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Notificación"
        verbose_name_plural = "Notificaciones"

    def __str__(self):
        return f"{self.title} - {self.user.username}"
