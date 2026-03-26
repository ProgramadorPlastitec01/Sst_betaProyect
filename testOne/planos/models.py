from django.db import models
from django.conf import settings


class UbicacionActivo(models.Model):
    """
    Almacena la posición de un activo dentro de un plano SVG.
    Cada vez que se mueve un activo se crea un nuevo registro
    y el anterior queda marcado como 'Inactivo' (historial).
    """

    ESTADO_CHOICES = [
        ('Activo',   'Activo'),
        ('Inactivo', 'Inactivo'),
    ]

    activo = models.ForeignKey(
        'gestion_activos.Asset',
        on_delete=models.CASCADE,
        related_name='ubicaciones_plano',
        verbose_name='Activo',
    )
    plano = models.CharField(
        max_length=20,
        verbose_name='Plano',
        db_index=True,
        help_text='Identificador del plano, ej: PL2P1',
    )
    posicion_x = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name='Posición X',
    )
    posicion_y = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name='Posición Y',
    )
    estado = models.CharField(
        max_length=10,
        choices=ESTADO_CHOICES,
        default='Activo',
        verbose_name='Estado',
        db_index=True,
    )
    fecha_registro = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Fecha de Registro',
    )
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='ubicaciones_registradas',
        verbose_name='Registrado por',
    )

    class Meta:
        verbose_name = 'Ubicación de Activo en Plano'
        verbose_name_plural = 'Ubicaciones de Activos en Planos'
        ordering = ['-fecha_registro']

    def __str__(self):
        return (
            f"{self.activo.code} → {self.plano} "
            f"({self.posicion_x}, {self.posicion_y}) [{self.estado}]"
        )
