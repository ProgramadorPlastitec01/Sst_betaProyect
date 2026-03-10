from django.db import models
from django.conf import settings
from django.utils import timezone
from datetime import timedelta


class TipoExtintor(models.Model):
    """
    Tipos/Clases de extintores gestionables desde Configuracion.
    Alimenta dinamicamente el campo tipo en ExtintorDetail.
    """
    nombre = models.CharField(max_length=150, unique=True, verbose_name="Nombre")
    activo = models.BooleanField(default=True, verbose_name="Activo")

    class Meta:
        verbose_name = "Tipo de Extintor"
        verbose_name_plural = "Tipos de Extintor"
        ordering = ['nombre']

    def __str__(self):
        return self.nombre


class AssetType(models.Model):
    """
    Tipos de activos gestionables.
    Solo gestionable desde el modulo de Configuracion.
    """
    name = models.CharField(max_length=100, unique=True, verbose_name="Nombre")
    description = models.TextField(blank=True, null=True, verbose_name="Descripcion")

    class Meta:
        verbose_name = "Tipo de Activo"
        verbose_name_plural = "Tipos de Activo"
        ordering = ['name']

    def __str__(self):
        return self.name


class Asset(models.Model):
    """Activo base del sistema."""
    code = models.CharField(max_length=50, unique=True, verbose_name="Codigo")
    asset_type = models.ForeignKey(
        AssetType,
        on_delete=models.PROTECT,
        verbose_name="Tipo de Activo",
        related_name="assets"
    )
    area = models.ForeignKey(
        'inspections.Area',
        on_delete=models.PROTECT,
        verbose_name="Area",
        related_name="assets"
    )
    plano = models.ForeignKey(
        'system_config.Plano',
        on_delete=models.SET_NULL,
        verbose_name="Plano",
        null=True,
        blank=True,
        related_name="activos"
    )
    fecha_adquisicion = models.DateField(blank=True, null=True, verbose_name="Fecha de Adquisicion")
    activo = models.BooleanField(default=True, verbose_name="Activo")
    # Solo se asigna True cuando se crea desde el flujo de Movimientos como reemplazo.
    # Los activos creados manualmente siempre son False.
    temporal = models.BooleanField(default=False, verbose_name="Es Temporal")
    observaciones = models.TextField(blank=True, null=True, verbose_name="Observaciones")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Activo"
        verbose_name_plural = "Activos"
        ordering = ['code']

    def __str__(self):
        return self.code

    @property
    def estado_actual(self):
        """
        Calcula el estado dinamicamente segun el tipo de activo.
        Para extintores: estado_movimiento tiene prioridad sobre la logica de fechas.
        """
        hoy = timezone.now().date()
        pronto = hoy + timedelta(days=30)

        # Extintor
        if hasattr(self, 'extintor_detail'):
            ext = self.extintor_detail
            # 1) Prioridad: estado de movimiento persistido (gestionado por flujo Movimientos)
            if ext.estado_movimiento == 'REEMPLAZADO':
                return 'REEMPLAZADO'
            if ext.estado_movimiento == 'FUERA_DE_SERVICIO':
                return 'FUERA_DE_SERVICIO'
            # 2) Logica original de fechas (sin cambios a lo existente)
            if ext.fecha_vencimiento:
                if ext.fecha_vencimiento < hoy:
                    return 'VENCIDO'
                if ext.fecha_vencimiento <= pronto:
                    return 'PROXIMO_A_VENCER'
            return 'ACTIVO'

        # Montacargas
        if hasattr(self, 'montacargas_detail'):
            mnt = self.montacargas_detail
            if mnt.fecha_proximo_mantenimiento:
                if mnt.fecha_proximo_mantenimiento < hoy:
                    return 'MANTENIMIENTO_VENCIDO'
                if mnt.fecha_proximo_mantenimiento <= pronto:
                    return 'PROXIMO_MANTENIMIENTO'
            return 'OPERATIVO'

        # Botiquin
        if hasattr(self, 'botiquin_detail'):
            bot = self.botiquin_detail
            if bot.fecha_proxima_revision:
                if bot.fecha_proxima_revision < hoy:
                    return 'REVISION_VENCIDA'
                if bot.fecha_proxima_revision <= pronto:
                    return 'PROXIMA_REVISION'
            return 'AL_DIA'

        return 'SIN_CLASIFICAR'

    @property
    def estado_label(self):
        """Etiqueta legible del estado."""
        labels = {
            'VENCIDO': 'Vencido',
            'PROXIMO_A_VENCER': 'Proximo a Vencer',
            'ACTIVO': 'Activo',
            'REEMPLAZADO': 'Reemplazado',
            'FUERA_DE_SERVICIO': 'Fuera de servicio',
            'MANTENIMIENTO_VENCIDO': 'Mantenimiento Vencido',
            'PROXIMO_MANTENIMIENTO': 'Proximo Mantenimiento',
            'OPERATIVO': 'Operativo',
            'REVISION_VENCIDA': 'Revisión Vencida',
            'PROXIMA_REVISION': 'Próxima Revisión',
            'AL_DIA': 'Al Día',
            'SIN_CLASIFICAR': 'Sin Clasificar',
        }
        return labels.get(self.estado_actual, self.estado_actual)

    @property
    def estado_css(self):
        """Clase CSS correspondiente al estado."""
        css = {
            'VENCIDO': 'badge-danger',
            'PROXIMO_A_VENCER': 'badge-warning',
            'ACTIVO': 'badge-success',
            'REEMPLAZADO': 'badge-warning',
            'FUERA_DE_SERVICIO': 'badge-secondary',
            'MANTENIMIENTO_VENCIDO': 'badge-danger',
            'PROXIMO_MANTENIMIENTO': 'badge-warning',
            'OPERATIVO': 'badge-success',
            'REVISION_VENCIDA': 'badge-danger',
            'PROXIMA_REVISION': 'badge-warning',
            'AL_DIA': 'badge-success',
            'SIN_CLASIFICAR': 'badge-secondary',
        }
        return css.get(self.estado_actual, 'badge-secondary')

    @property
    def tipo_nombre(self):
        return self.asset_type.name if self.asset_type else ''

    def get_detail_data(self):
        """Retorna el objeto de detalle (extintor o montacargas) si existe."""
        if hasattr(self, 'extintor_detail'):
            return self.extintor_detail
        if hasattr(self, 'montacargas_detail'):
            return self.montacargas_detail
        return None

    def get_temporal_activo(self):
        """
        Para extintores en estado REEMPLAZADO: retorna el activo temporal
        actualmente asociado (el del ultimo movimiento tipo 'salida').
        """
        ultimo = self.movimientos.filter(
            tipo_movimiento='salida',
            activo_relacionado__isnull=False
        ).select_related('activo_relacionado__extintor_detail').order_by('-created_at').first()
        if ultimo and ultimo.activo_relacionado:
            return ultimo.activo_relacionado
        return None


class ExtintorDetail(models.Model):
    """Datos especificos de un activo tipo Extintor."""

    ESTADO_MOVIMIENTO_CHOICES = [
        ('NORMAL', 'Normal'),
        ('REEMPLAZADO', 'Reemplazado'),
        ('FUERA_DE_SERVICIO', 'Fuera de servicio'),
    ]

    asset = models.OneToOneField(
        Asset,
        on_delete=models.CASCADE,
        related_name='extintor_detail',
        verbose_name="Activo"
    )
    tipo_agente = models.ForeignKey(
        TipoExtintor,
        on_delete=models.PROTECT,
        verbose_name="Tipo/Clase de Extintor",
        null=True,
        blank=True
    )
    capacidad_kg = models.DecimalField(
        max_digits=6, decimal_places=2,
        verbose_name="Capacidad (kg/lbs)"
    )
    fecha_recarga = models.DateField(verbose_name="Fecha de Ultima Recarga")
    fecha_vencimiento = models.DateField(verbose_name="Fecha de Vencimiento")
    # Gestionado automaticamente por el flujo de Movimientos. No editar manualmente.
    estado_movimiento = models.CharField(
        max_length=20,
        choices=ESTADO_MOVIMIENTO_CHOICES,
        default='NORMAL',
        verbose_name="Estado de Movimiento"
    )

    class Meta:
        verbose_name = "Detalle de Extintor"
        verbose_name_plural = "Detalles de Extintor"

    def __str__(self):
        return f"Extintor: {self.asset.code}"


class MontacargasDetail(models.Model):
    """Datos especificos de un activo tipo Montacargas."""
    TIPO_MONTACARGAS_CHOICES = [
        ('Combustible', 'Combustible'),
        ('Electrico', 'Eléctrico'),
    ]

    asset = models.OneToOneField(
        Asset,
        on_delete=models.CASCADE,
        related_name='montacargas_detail',
        verbose_name="Activo"
    )
    marca = models.CharField(max_length=100, verbose_name="Marca")
    modelo = models.CharField(max_length=100, verbose_name="Modelo")
    numero_serie = models.CharField(max_length=100, verbose_name="Numero de Serie")
    tipo_montacargas = models.CharField(
        max_length=50,
        choices=TIPO_MONTACARGAS_CHOICES,
        default='Combustible',
        verbose_name="Tipo de Montacargas"
    )
    capacidad_carga_kg = models.DecimalField(
        max_digits=8, decimal_places=2,
        verbose_name="Capacidad de Carga (kg)"
    )
    fecha_ultimo_mantenimiento = models.DateField(verbose_name="Ultimo Mantenimiento")
    fecha_proximo_mantenimiento = models.DateField(verbose_name="Proximo Mantenimiento")

    class Meta:
        verbose_name = "Detalle de Montacargas"
        verbose_name_plural = "Detalles de Montacargas"

    def __str__(self):
        return f"Montacargas: {self.asset.code}"


class BotiquinDetail(models.Model):
    """Datos especificos de un activo tipo Botiquin."""

    asset = models.OneToOneField(
        Asset,
        on_delete=models.CASCADE,
        related_name='botiquin_detail',
        verbose_name="Activo"
    )
    fecha_ultima_revision = models.DateField(
        verbose_name="Fecha de Última Revisión / Recarga"
    )
    fecha_proxima_revision = models.DateField(
        verbose_name="Próxima Revisión / Recarga",
        blank=True,
        null=True,
        help_text="Se calcula automáticamente: +1 año desde la fecha de última revisión."
    )

    class Meta:
        verbose_name = "Detalle de Botiquín"
        verbose_name_plural = "Detalles de Botiquín"

    def save(self, *args, **kwargs):
        # Calcular automáticamente la próxima revisión (+1 año)
        if self.fecha_ultima_revision:
            from dateutil.relativedelta import relativedelta
            self.fecha_proxima_revision = self.fecha_ultima_revision + relativedelta(years=1)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Botiquín: {self.asset.code}"


class MovimientoActivo(models.Model):
    """
    Trazabilidad de movimientos de activos (extintores).
    Registra salidas, reemplazos con temporal y retornos.
    Nunca se eliminan registros historicos.
    """
    TIPO_CHOICES = [
        ('salida', 'Salida'),
        ('reemplazo', 'Reemplazo con Temporal'),
        ('retorno', 'Retorno del Original'),
        ('baja_temporal', 'Baja de Temporal'),
    ]

    activo = models.ForeignKey(
        Asset,
        on_delete=models.PROTECT,
        related_name='movimientos',
        verbose_name="Activo"
    )
    tipo_movimiento = models.CharField(
        max_length=20,
        choices=TIPO_CHOICES,
        verbose_name="Tipo de Movimiento"
    )
    activo_relacionado = models.ForeignKey(
        Asset,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='movimientos_como_relacionado',
        verbose_name="Activo Relacionado",
        help_text="Temporal asociado en caso de reemplazo."
    )
    fecha = models.DateField(verbose_name="Fecha del Movimiento")
    responsable = models.CharField(max_length=200, verbose_name="Responsable")
    motivo = models.TextField(blank=True, verbose_name="Motivo")
    observaciones = models.TextField(blank=True, verbose_name="Observaciones")
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='movimientos_registrados',
        verbose_name="Registrado por"
    )

    class Meta:
        verbose_name = "Movimiento de Activo"
        verbose_name_plural = "Movimientos de Activos"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.get_tipo_movimiento_display()} - {self.activo.code} ({self.fecha})"
