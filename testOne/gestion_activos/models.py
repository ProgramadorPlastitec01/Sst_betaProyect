from django.db import models
from django.utils import timezone
from datetime import timedelta


class TipoExtintor(models.Model):
    """
    Tipos/Clases de extintores gestionables desde Configuración.
    Alimenta dinmámicamente el campo tipo en ExtintorDetail.
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
    Solo gestionable desde el módulo de Configuración.
    """
    name = models.CharField(max_length=100, unique=True, verbose_name="Nombre")
    description = models.TextField(blank=True, null=True, verbose_name="Descripción")

    class Meta:
        verbose_name = "Tipo de Activo"
        verbose_name_plural = "Tipos de Activo"
        ordering = ['name']

    def __str__(self):
        return self.name


class Asset(models.Model):
    """Activo base del sistema."""
    code = models.CharField(max_length=50, unique=True, verbose_name="Código")
    asset_type = models.ForeignKey(
        AssetType,
        on_delete=models.PROTECT,
        verbose_name="Tipo de Activo",
        related_name="assets"
    )
    area = models.ForeignKey(
        'inspections.Area',
        on_delete=models.PROTECT,
        verbose_name="Área",
        related_name="assets"
    )
    fecha_adquisicion = models.DateField(blank=True, null=True, verbose_name="Fecha de Adquisición")
    activo = models.BooleanField(default=True, verbose_name="Activo")
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
        Calcula el estado dinámicamente según el tipo de activo.
        No se almacena en base de datos.
        """
        hoy = timezone.now().date()
        pronto = hoy + timedelta(days=30)

        # Extintor
        if hasattr(self, 'extintor_detail'):
            ext = self.extintor_detail
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

        return 'SIN_CLASIFICAR'

    @property
    def estado_label(self):
        """Etiqueta legible del estado."""
        labels = {
            'VENCIDO': 'Vencido',
            'PROXIMO_A_VENCER': 'Próximo a Vencer',
            'ACTIVO': 'Activo',
            'MANTENIMIENTO_VENCIDO': 'Mantenimiento Vencido',
            'PROXIMO_MANTENIMIENTO': 'Próximo Mantenimiento',
            'OPERATIVO': 'Operativo',
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
            'MANTENIMIENTO_VENCIDO': 'badge-danger',
            'PROXIMO_MANTENIMIENTO': 'badge-warning',
            'OPERATIVO': 'badge-success',
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


class ExtintorDetail(models.Model):
    """Datos específicos de un activo tipo Extintor."""
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
    fecha_recarga = models.DateField(verbose_name="Fecha de Última Recarga")
    fecha_vencimiento = models.DateField(verbose_name="Fecha de Vencimiento")

    class Meta:
        verbose_name = "Detalle de Extintor"
        verbose_name_plural = "Detalles de Extintor"

    def __str__(self):
        return f"Extintor: {self.asset.code}"


class MontacargasDetail(models.Model):
    """Datos específicos de un activo tipo Montacargas."""
    asset = models.OneToOneField(
        Asset,
        on_delete=models.CASCADE,
        related_name='montacargas_detail',
        verbose_name="Activo"
    )
    marca = models.CharField(max_length=100, verbose_name="Marca")
    modelo = models.CharField(max_length=100, verbose_name="Modelo")
    numero_serie = models.CharField(max_length=100, verbose_name="Número de Serie")
    capacidad_carga_kg = models.DecimalField(
        max_digits=8, decimal_places=2,
        verbose_name="Capacidad de Carga (kg)"
    )
    fecha_ultimo_mantenimiento = models.DateField(verbose_name="Último Mantenimiento")
    fecha_proximo_mantenimiento = models.DateField(verbose_name="Próximo Mantenimiento")

    class Meta:
        verbose_name = "Detalle de Montacargas"
        verbose_name_plural = "Detalles de Montacargas"

    def __str__(self):
        return f"Montacargas: {self.asset.code}"
