from django.db import models

class SystemConfig(models.Model):
    CONFIG_TYPES = [
        ('string', 'Texto'),
        ('number', 'Número'),
        ('boolean', 'Booleano'),
    ]

    key = models.CharField(max_length=100, unique=True, verbose_name="Clave")
    value = models.CharField(max_length=255, verbose_name="Valor")
    description = models.TextField(blank=True, verbose_name="Descripción")
    config_type = models.CharField(max_length=20, choices=CONFIG_TYPES, default='string', verbose_name="Tipo de Dato")
    category = models.CharField(max_length=50, default='general', verbose_name="Categoría")
    is_editable = models.BooleanField(default=True, verbose_name="Editable")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Última Actualización")

    def __str__(self):
        return f"{self.key} ({self.category})"

    class Meta:
        verbose_name = "Configuración del Sistema"
        verbose_name_plural = "Configuraciones del Sistema"
        ordering = ['category', 'key']

    def get_typed_value(self):
        if self.config_type == 'number':
            try:
                # Simple integer conversion first, could extend to float if needed later
                return int(float(self.value))
            except ValueError:
                return 0
        elif self.config_type == 'boolean':
            return self.value.lower() == 'true'
        return self.value

    @classmethod
    def get_value(cls, key, default=None):
        try:
            return cls.objects.get(key=key).get_typed_value()
        except cls.DoesNotExist:
            return default
