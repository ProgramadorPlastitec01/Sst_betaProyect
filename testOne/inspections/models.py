from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator

# Existing InspectionSchedule Model
class InspectionSchedule(models.Model):
    FREQUENCY_CHOICES = [
        ('Mensual', 'Mensual'),
        ('Trimestral', 'Trimestral'),
        ('Cuatrimestral', 'Cuatrimestral'),
        ('Semestral', 'Semestral'),
        ('Anual', 'Anual'),
    ]

    STATUS_CHOICES = [
        ('Programada', 'Programada'),
        ('Realizada', 'Realizada'),
        ('Pendiente', 'Pendiente'),
    ]

    year = models.IntegerField(verbose_name="Año de Programación")
    area = models.CharField(max_length=200, verbose_name="Área a Inspeccionar")
    inspection_type = models.CharField(max_length=200, verbose_name="Tipo de Inspección")
    frequency = models.CharField(max_length=20, choices=FREQUENCY_CHOICES, verbose_name="Frecuencia")
    scheduled_date = models.DateField(verbose_name="Fecha Programada")
    responsible = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='scheduled_inspections',
        verbose_name="Responsable"
    )
    status = models.CharField(
        max_length=20, 
        choices=STATUS_CHOICES, 
        default='Programada',
        verbose_name="Estado"
    )
    observations = models.TextField(blank=True, null=True, verbose_name="Observaciones")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.inspection_type} - {self.area} ({self.scheduled_date})"

    class Meta:
        verbose_name = "Cronograma de Inspección"
        verbose_name_plural = "Cronogramas de Inspección"
        ordering = ['scheduled_date']

    def get_absolute_url_result(self):
        """Returns the URL of the actual inspection registered for this schedule item."""
        from django.urls import reverse
        if self.status == 'Realizada':
            # Check each related set (added via BaseInspection link)
            if hasattr(self, 'extinguisherinspection_actual_inspections'):
                resp = self.extinguisherinspection_actual_inspections.first()
                if resp: return reverse('extinguisher_detail', args=[resp.pk])
            
            if hasattr(self, 'firstaidinspection_actual_inspections'):
                resp = self.firstaidinspection_actual_inspections.first()
                if resp: return reverse('first_aid_detail', args=[resp.pk])
                
            if hasattr(self, 'processinspection_actual_inspections'):
                resp = self.processinspection_actual_inspections.first()
                if resp: return reverse('process_detail', args=[resp.pk])
                
            if hasattr(self, 'storageinspection_actual_inspections'):
                resp = self.storageinspection_actual_inspections.first()
                if resp: return reverse('storage_detail', args=[resp.pk])

            if hasattr(self, 'forkliftinspection_actual_inspections'):
                resp = self.forkliftinspection_actual_inspections.first()
                if resp: return reverse('forklift_detail', args=[resp.pk])
        return None

# Base Abstract Model for Inspections
class BaseInspection(models.Model):
    STATUS_CHOICES = [
        ('Cumple', 'Cumple'),
        ('No Cumple', 'No Cumple'),
        ('No Aplica', 'No Aplica'),
    ]

    inspection_date = models.DateField(verbose_name="Fecha de Inspección")
    area = models.CharField(max_length=200, verbose_name="Área/Ubicación")
    inspector = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="%(class)s_inspections",
        verbose_name="Inspector"
    )
    schedule_item = models.ForeignKey(
        'InspectionSchedule',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Ítem del Cronograma",
        related_name="%(class)s_actual_inspections"
    )
    general_status = models.CharField(
        max_length=20, 
        choices=STATUS_CHOICES, 
        default='Cumple',
        verbose_name="Estado General"
    )
    observations = models.TextField(blank=True, null=True, verbose_name="Observaciones Generales")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True
        ordering = ['-inspection_date']

    def __str__(self):
        return f"{self._meta.verbose_name} - {self.area} ({self.inspection_date})"

# 1. Extinguisher Inspection (R-RH-SST-019)
class ExtinguisherInspection(BaseInspection):
    ROLE_CHOICES = [
        ('Brigadista', 'Brigadista'),
        ('Equipo SST', 'Equipo SST'),
        ('Copasst', 'Copasst'),
    ]
    inspector_role = models.CharField(
        max_length=20, 
        choices=ROLE_CHOICES, 
        default='Equipo SST',
        verbose_name="Rol del Inspector"
    )

    class Meta(BaseInspection.Meta):
        verbose_name = "Inspección de Extintores"
        verbose_name_plural = "Inspecciones de Extintores"

class ExtinguisherItem(models.Model):
    TYPE_CHOICES = [
        ('PQS', 'Polvo Químico Seco'),
        ('CO2', 'Dióxido de Carbono'),
        ('SOLKAFLAM', 'Solkaflam'),
        ('AGUA', 'Agua a Presión'),
    ]
    STATUS_CHOICES = [
        ('Bueno', 'Bueno'),
        ('Malo', 'Malo'),
        ('Recargar', 'Recargar'),
    ]

    inspection = models.ForeignKey(ExtinguisherInspection, related_name='items', on_delete=models.CASCADE)
    location = models.CharField(max_length=100, verbose_name="Ubicación Específica")
    extinguisher_type = models.CharField(max_length=20, choices=TYPE_CHOICES, verbose_name="Tipo")
    capacity = models.CharField(max_length=50, verbose_name="Capacidad (lbs/kg)")
    last_recharge_date = models.DateField(verbose_name="Última Recarga", blank=True, null=True)
    next_recharge_date = models.DateField(verbose_name="Próxima Recarga", blank=True, null=True)
    
    # Checklist items specific to extinguishers
    pressure_gauge_ok = models.BooleanField(default=True, verbose_name="Manómetro")
    safety_pin_ok = models.BooleanField(default=True, verbose_name="Seguro/Pasador")
    hose_nozzle_ok = models.BooleanField(default=True, verbose_name="Manguera/Boquilla")
    signage_ok = models.BooleanField(default=True, verbose_name="Señalización")
    access_ok = models.BooleanField(default=True, verbose_name="Acceso Libre")
    label_ok = models.BooleanField(default=True, verbose_name="Etiqueta Legible")

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Bueno', verbose_name="Estado")
    observations = models.CharField(max_length=255, blank=True, verbose_name="Observaciones")

# 2. First Aid Inspection (R-RH-SST-020)
class FirstAidInspection(BaseInspection):
    ROLE_CHOICES = [
        ('Brigadista', 'Brigadista'),
        ('Equipo SST', 'Equipo SST'),
        ('Copasst', 'Copasst'),
    ]
    inspector_role = models.CharField(
        max_length=20, 
        choices=ROLE_CHOICES, 
        default='Equipo SST',
        verbose_name="Rol del Inspector"
    )

    class Meta(BaseInspection.Meta):
        verbose_name = "Inspección de Botiquín"
        verbose_name_plural = "Inspecciones de Botiquines"

class FirstAidItem(models.Model):
    STATUS_CHOICES = [
        ('Existe', 'Existe'),
        ('No Existe', 'No Existe'),
    ]

    inspection = models.ForeignKey(FirstAidInspection, related_name='items', on_delete=models.CASCADE)
    element_name = models.CharField(max_length=100, verbose_name="Nombre del Elemento")
    quantity = models.PositiveIntegerField(default=1, verbose_name="Cantidad (Unidad)")
    expiration_date = models.DateField(verbose_name="Fecha de Vencimiento", blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Existe', verbose_name="Estado")
    observations = models.CharField(max_length=255, blank=True, verbose_name="Observaciones")

# 3. Process Facility Inspection (R-RH-SST-030)
class ProcessInspection(BaseInspection):
    ROLE_CHOICES = [
        ('Brigadista', 'Brigadista'),
        ('Equipo SST', 'Equipo SST'),
        ('Copasst', 'Copasst'),
    ]
    inspector_role = models.CharField(
        max_length=20, 
        choices=ROLE_CHOICES, 
        default='Equipo SST',
        verbose_name="Rol del Inspector"
    )
    inspected_process = models.CharField(max_length=200, verbose_name="Proceso Inspeccionado", blank=True, null=True)

    class Meta(BaseInspection.Meta):
        verbose_name = "Inspección de Procesos"
        verbose_name_plural = "Inspecciones de Procesos"

class ProcessCheckItem(models.Model):
    RESPONSE_CHOICES = [
        ('Si', 'Si'),
        ('No', 'No'),
        ('NA', 'No Aplica'),
    ]
    STATUS_CHOICES = [
        ('Bueno', 'Bueno'),
        ('Regular', 'Regular'),
        ('Malo', 'Malo'),
        ('NA', 'No Aplica'),
    ]

    inspection = models.ForeignKey(ProcessInspection, related_name='items', on_delete=models.CASCADE)
    question = models.CharField(max_length=500, verbose_name="Ítem a Evaluar")
    response = models.CharField(max_length=10, choices=RESPONSE_CHOICES, default='Si', verbose_name="Cumple")
    item_status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Bueno', verbose_name="Estado")
    observations = models.CharField(max_length=255, blank=True, verbose_name="Observaciones")

# 4. Storage Area Inspection (R-RH-SST-031)
class StorageInspection(BaseInspection):
    ROLE_CHOICES = [
        ('Brigadista', 'Brigadista'),
        ('Equipo SST', 'Equipo SST'),
        ('Copasst', 'Copasst'),
    ]
    inspector_role = models.CharField(
        max_length=20, 
        choices=ROLE_CHOICES, 
        default='Equipo SST',
        verbose_name="Rol del Inspector"
    )
    inspected_process = models.CharField(max_length=200, verbose_name="Proceso Inspeccionado", blank=True, null=True)

    class Meta(BaseInspection.Meta):
        verbose_name = "Inspección de Almacenamiento"
        verbose_name_plural = "Inspecciones de Almacenamiento"

class StorageCheckItem(models.Model):
    RESPONSE_CHOICES = [
        ('Si', 'Si'),
        ('No', 'No'),
        ('NA', 'No Aplica'),
    ]
    STATUS_CHOICES = [
        ('Bueno', 'Bueno'),
        ('Regular', 'Regular'),
        ('Malo', 'Malo'),
        ('NA', 'No Aplica'),
    ]

    inspection = models.ForeignKey(StorageInspection, related_name='items', on_delete=models.CASCADE)
    question = models.CharField(max_length=500, verbose_name="Ítem a Evaluar")
    response = models.CharField(max_length=10, choices=RESPONSE_CHOICES, default='Si', verbose_name="Cumple")
    item_status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Bueno', verbose_name="Estado")
    observations = models.CharField(max_length=255, blank=True, verbose_name="Observaciones")

# 5. Forklift Inspection (R-RH-SST-022)
class ForkliftInspection(BaseInspection):
    FORKLIFT_TYPE_CHOICES = [
        ('Combustible', 'Montacarga de Combustible'),
        ('Electrico', 'Montacarga Eléctrico'),
    ]
    forklift_type = models.CharField(
        max_length=20, 
        choices=FORKLIFT_TYPE_CHOICES, 
        default='Combustible',
        verbose_name="Tipo de Montacarga"
    )

    class Meta(BaseInspection.Meta):
        verbose_name = "Inspección de Montacargas"
        verbose_name_plural = "Inspecciones de Montacargas"

class ForkliftCheckItem(models.Model):
    RESPONSE_CHOICES = [
        ('Si', 'Si'),
        ('No', 'No'),
        ('NA', 'N/A'),
    ]
    inspection = models.ForeignKey(ForkliftInspection, related_name='items', on_delete=models.CASCADE)
    question = models.CharField(max_length=500, verbose_name="Ítem a Evaluar")
    response = models.CharField(max_length=10, choices=RESPONSE_CHOICES, default='Si', verbose_name="Cumple")
    observations = models.CharField(max_length=255, blank=True, verbose_name="Observación")
