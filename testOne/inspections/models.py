from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator
from datetime import date, timedelta
from dateutil.relativedelta import relativedelta
from django.contrib.contenttypes.fields import GenericForeignKey, GenericRelation
from django.contrib.contenttypes.models import ContentType

# Area Model - Standardized areas for inspections
class Area(models.Model):
    """
    Standardized areas for the organization.
    Used across all inspection modules to ensure consistency.
    """
    name = models.CharField(max_length=200, unique=True, verbose_name="Nombre del Área")
    is_active = models.BooleanField(default=True, verbose_name="Activa")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Área"
        verbose_name_plural = "Áreas"
        ordering = ['name']

    def __str__(self):
        return self.name

# Existing InspectionSchedule Model
class InspectionSchedule(models.Model):
    FREQUENCY_CHOICES = [
        ('Mensual', 'Mensual'),
        ('Bimestral', 'Bimestral'),
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

    year = models.IntegerField(verbose_name="Año de Programación", blank=True, null=True)
    area = models.ForeignKey(
        'Area',
        on_delete=models.PROTECT,
        verbose_name="Área a Inspeccionar",
        help_text="Seleccione el área donde se realizará la inspección"
    )
    inspection_type = models.CharField(max_length=200, verbose_name="Tipo de Inspección")
    frequency = models.CharField(max_length=20, choices=FREQUENCY_CHOICES, verbose_name="Frecuencia")
    scheduled_date = models.DateField(verbose_name="Fecha Programada")
    responsible = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='scheduled_inspections',
        verbose_name="Responsable",
        blank=True,
        null=True
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

    def save(self, *args, **kwargs):
        if self.scheduled_date:
            self.year = self.scheduled_date.year
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.inspection_type} - {self.area} ({self.scheduled_date})"

    class Meta:
        verbose_name = "Cronograma de Inspección"
        verbose_name_plural = "Cronogramas de Inspección"
        ordering = ['scheduled_date']

    def get_actual_inspection(self):
        """Helper to find the actual inspection object related to this schedule item."""
        if hasattr(self, 'extinguisherinspection_actual_inspections'):
            obj = self.extinguisherinspection_actual_inspections.first()
            if obj: return obj
        if hasattr(self, 'firstaidinspection_actual_inspections'):
            obj = self.firstaidinspection_actual_inspections.first()
            if obj: return obj
        if hasattr(self, 'processinspection_actual_inspections'):
            obj = self.processinspection_actual_inspections.first()
            if obj: return obj
        if hasattr(self, 'storageinspection_actual_inspections'):
            obj = self.storageinspection_actual_inspections.first()
            if obj: return obj
        if hasattr(self, 'forkliftinspection_actual_inspections'):
            obj = self.forkliftinspection_actual_inspections.first()
            if obj: return obj
        return None

    def get_absolute_url_result(self):
        """Returns the URL of the actual inspection registered for this schedule item."""
        from django.urls import reverse
        if self.status == 'Realizada':
            insp = self.get_actual_inspection()
            if insp:
                cls_name = insp.__class__.__name__
                if 'Extinguisher' in cls_name: return reverse('extinguisher_detail', args=[insp.pk])
                if 'FirstAid' in cls_name: return reverse('first_aid_detail', args=[insp.pk])
                if 'Process' in cls_name: return reverse('process_detail', args=[insp.pk])
                if 'Storage' in cls_name: return reverse('storage_detail', args=[insp.pk])
                if 'Forklift' in cls_name: return reverse('forklift_detail', args=[insp.pk])
        return None

    @property
    def is_executable(self):
        """Determines if the inspection can be executed today (on or after the scheduled date)."""
        if self.status == 'Realizada':
            return False
        return date.today() >= self.scheduled_date

    @property
    def is_overdue(self):
        """Determines if the inspection is overdue (past scheduled date, not completed)."""
        return date.today() > self.scheduled_date and self.status != 'Realizada'

    @property
    def is_upcoming(self):
        """Determines if the inspection is upcoming (within the next 7 days)."""
        today = date.today()
        return today <= self.scheduled_date <= today + timedelta(days=7) and self.status != 'Realizada'

    def generate_next_schedule(self):
        """
        Generates the next inspection schedule based on frequency.
        Should be called when this inspection is completed.
        """
        if not self.frequency or self.frequency == 'Única':
            return None

        next_date = self.scheduled_date

        if self.frequency == 'Mensual':
            next_date += relativedelta(months=1)
        elif self.frequency == 'Bimestral':
            next_date += relativedelta(months=2)
        elif self.frequency == 'Trimestral':
            next_date += relativedelta(months=3)
        elif self.frequency == 'Cuatrimestral':
            next_date += relativedelta(months=4)
        elif self.frequency == 'Semestral':
            next_date += relativedelta(months=6)
        elif self.frequency == 'Anual':
            next_date += relativedelta(years=1)

        # Create new schedule only if it doesn't already exist
        existing = InspectionSchedule.objects.filter(
            area=self.area,
            inspection_type=self.inspection_type,
            scheduled_date=next_date
        ).exists()

        if not existing:
            new_schedule = InspectionSchedule.objects.create(
                year=next_date.year,
                area=self.area,
                inspection_type=self.inspection_type,
                frequency=self.frequency,
                scheduled_date=next_date,
                responsible=self.responsible,
                status='Programada',
                observations=f"Generada automáticamente tras realizar la inspección del {self.scheduled_date.strftime('%d/%m/%Y')}"
            )
            return new_schedule
        return None

    @property
    def status_label(self):
        if self.status == 'Realizada':
            insp = self.get_actual_inspection()
            if insp:
                # Check for 'status' field (workflow)
                if hasattr(insp, 'status'):
                    # Mapeo de estados internos a etiquetas visibles
                    st = insp.status
                    if st == 'Programada': return 'Programada'
                    if st == 'En proceso': return 'En proceso'
                    if st == 'Seguimiento en proceso': return 'Seguimiento en proceso'
                    if st == 'Cerrada': return 'Cerrada'
                    if st == 'Cerrada con seguimientos': return 'Cerrada con seguimientos'
                    
                    # Fallback para estados viejos que puedan quedar en DB
                    if st == 'Cerrada con Hallazgos': return 'Seguimiento en proceso'
                    if st == 'Pendiente de Firmas': return 'En proceso'
                    if st == 'Pendiente': return 'Programada'
                    
                    return st
                
                # Fallback to general_status
                if hasattr(insp, 'general_status'):
                     gs = insp.general_status
                     if gs == 'No Cumple': return 'Seguimiento en proceso' # Antes era Cerrada con Hallazgos
                     if gs == 'Cumple': return 'Cerrada'
                     return gs
            return "Programada"
        # Non-realized - Check if overdue
        if self.scheduled_date < date.today():
            return "Vencida"
        return "Programada"

    @property
    def status_css_class(self):
        if self.status == 'Realizada':
            insp = self.get_actual_inspection()
            if insp:
                if hasattr(insp, 'status'):
                    st = insp.status
                    if st in ['Cerrada', 'Cerrada con seguimientos']: return 'badge-success'
                    if st in ['Seguimiento en proceso', 'Cerrada con Hallazgos']: return 'badge-orange'
                    if st in ['En proceso', 'Pendiente de Firmas']: return 'badge-primary'
                    if st == 'Programada': return 'badge-secondary'
                    return 'badge-secondary'
                
                if hasattr(insp, 'general_status'):
                    gs = insp.general_status
                    if gs == 'Cumple': return 'badge-success'
                    if gs == 'No Cumple': return 'badge-orange-dark'
            return 'badge-secondary'
        if self.scheduled_date < date.today():
             return 'badge-danger'
        return 'badge-secondary'

    @property
    def is_overdue(self):
         return self.status != 'Realizada' and self.scheduled_date < date.today()
    
    @property
    def is_upcoming(self):
         return self.status != 'Realizada' and self.scheduled_date > date.today()

    @property
    def is_executable(self):
         # If 'Realizada' but orphan (no actual inspection), treat as executable if date passed
         if self.status == 'Realizada' and not self.get_actual_inspection():
             return self.scheduled_date <= date.today()
         return self.scheduled_date <= date.today() and self.status != 'Realizada'

    def get_module_url(self):
        """Returns the URL for the corresponding inspection module list."""
        from django.urls import reverse
        t = self.inspection_type.lower()
        url = None
        
        # Map types to module list URLs
        if 'extintor' in t: url = reverse('extinguisher_list')
        elif 'botiquin' in t: url = reverse('first_aid_list')
        elif 'proceso' in t or 'instalacion' in t: url = reverse('process_list')
        elif 'almacen' in t or 'storage' in t: url = reverse('storage_list')
        elif 'montacarga' in t: url = reverse('forklift_list')
        
        if url:
             return f"{url}?schedule_id={self.id}"
        
        # Fallback to schedule list with filters
        return reverse('inspection_list') + f"?year={self.year}&area={self.area.id}"

# Base Abstract Model for Inspections
class BaseInspection(models.Model):
    STATUS_CHOICES = [
        ('Cumple', 'Cumple'),
        ('No Cumple', 'No Cumple'),
        ('No Aplica', 'No Aplica'),
    ]

    inspection_date = models.DateField(verbose_name="Fecha de Inspección")
    area = models.ForeignKey(
        'Area',
        on_delete=models.PROTECT,
        verbose_name="Área/Ubicación",
        help_text="Seleccione el área inspeccionada"
    )
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
    
    # Generic relation for evidence
    evidences = GenericRelation('InspectionEvidence')

    class Meta:
        abstract = True
        ordering = ['-inspection_date']

    def __str__(self):
        return f"{self._meta.verbose_name} - {self.area} ({self.inspection_date})"

class InspectionEvidence(models.Model):
    """
    Modelo genérico para almacenar evidencias fotográficas de inspecciones,
    ítems de verificación o seguimientos.
    """
    # Relación Genérica
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')
    
    image = models.ImageField(upload_to='inspections/evidence/%Y/%m/%d/', verbose_name="Imagen de Evidencia")
    description = models.CharField(max_length=255, blank=True, null=True, verbose_name="Descripción o Hallazgo")
    
    uploaded_at = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de Carga")
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        verbose_name="Cargado por"
    )

    class Meta:
        verbose_name = "Evidencia de Inspección"
        verbose_name_plural = "Evidencias de Inspección"
        ordering = ['-uploaded_at']

    def __str__(self):
        return f"Evidencia {self.id} de {self.content_object}"

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
    
    INSPECTION_STATUS_CHOICES = [
        ('Programada', 'Programada'),
        ('En proceso', 'En proceso'),
        ('Seguimiento en proceso', 'Seguimiento en proceso'),
        ('Cerrada', 'Cerrada'),
        ('Cerrada con seguimientos', 'Cerrada con seguimientos'),
    ]
    status = models.CharField(
        max_length=30, 
        choices=INSPECTION_STATUS_CHOICES, 
        default='Programada', 
        verbose_name="Estado de Inspección"
    )

    def get_participants(self):
        """Returns unique users who registered items or is the main inspector."""
        from django.contrib.auth import get_user_model
        User = get_user_model()
        user_ids = set(self.items.values_list('registered_by', flat=True))
        user_ids.discard(None)
        if self.inspector:
            user_ids.add(self.inspector.id)
        return User.objects.filter(id__in=user_ids)
    
    parent_inspection = models.ForeignKey(
        'self', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='follow_ups',
        verbose_name="Inspección de Origen"
    )
    asset = models.ForeignKey(
        'gestion_activos.Asset',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Activo Relacionado",
        help_text="Activo del inventario asociado a esta inspección",
        related_name='extinguisher_inspections'
    )

    def get_total_follow_ups_count(self):
        """
        Cuenta recursivamente TODOS los seguimientos asociados a esta inspección.
        Incluye hijos directos, nietos, bisnietos, etc.
        """
        count = 0
        for child in self.follow_ups.all():
            count += 1  # Contar el hijo directo
            count += child.get_total_follow_ups_count()  # Contar sus descendientes
        return count

    @property
    def get_detail_url(self):
        from django.urls import reverse
        return reverse('extinguisher_detail', args=[self.pk])

    class Meta(BaseInspection.Meta):
        verbose_name = "Inspección de Extintores"
        verbose_name_plural = "Inspecciones de Extintores"


class InspectionSignature(models.Model):
    inspection = models.ForeignKey(ExtinguisherInspection, related_name='signatures', on_delete=models.CASCADE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, verbose_name="Firmante")
    signature = models.TextField(verbose_name="Firma Base64 (Snapshot)")
    signed_at = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de Firma")

    class Meta:
        verbose_name = "Firma de Inspección"
        verbose_name_plural = "Firmas de Inspección"
        unique_together = ('inspection', 'user')

class ExtinguisherItem(models.Model):
    STATUS_CHOICES = [
        ('Bueno', 'Bueno'),
        ('Malo', 'Malo'),
        ('Recargar', 'Recargar'),
    ]

    inspection = models.ForeignKey(ExtinguisherInspection, related_name='items', on_delete=models.CASCADE)
    asset = models.ForeignKey(
        'gestion_activos.Asset',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        verbose_name="Extintor (Inventario)",
        related_name='extinguisher_items'
    )

    # Checklist items specific to extinguishers
    pressure_gauge_ok = models.BooleanField(default=True, verbose_name="Manómetro")
    safety_pin_ok = models.BooleanField(default=True, verbose_name="Seguro/Pasador")
    hose_nozzle_ok = models.BooleanField(default=True, verbose_name="Manguera/Boquilla")
    signage_ok = models.BooleanField(default=True, verbose_name="Señalización")
    access_ok = models.BooleanField(default=True, verbose_name="Acceso Libre")
    label_ok = models.BooleanField(default=True, verbose_name="Etiqueta Legible")

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Bueno', verbose_name="Estado")
    observations = models.CharField(max_length=255, blank=True, verbose_name="Observaciones")
    fecha_recarga_realizada = models.DateField(
        null=True, blank=True,
        verbose_name="Fecha de Recarga Realizada",
        help_text="Completar solo si se realizó una recarga durante esta inspección"
    )
    fecha_proxima_recarga = models.DateField(
        null=True, blank=True,
        verbose_name="Próxima Recarga",
        help_text="Calculado: 1 año después de la recarga realizada"
    )
    registered_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Registrado por")

    evidences = GenericRelation('InspectionEvidence')

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
    asset = models.ForeignKey(
        'gestion_activos.Asset',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Botiquín",
        related_name="first_aid_inspections"
    )

    INSPECTION_STATUS_CHOICES = [
        ('Programada', 'Programada'),
        ('En proceso', 'En proceso'),
        ('Seguimiento en proceso', 'Seguimiento en proceso'),
        ('Cerrada', 'Cerrada'),
        ('Cerrada con seguimientos', 'Cerrada con seguimientos'),
    ]
    status = models.CharField(
        max_length=30, 
        choices=INSPECTION_STATUS_CHOICES, 
        default='Programada', 
        verbose_name="Estado de Inspección"
    )

    def get_participants(self):
        from django.contrib.auth import get_user_model
        User = get_user_model()
        user_ids = set(self.items.values_list('registered_by', flat=True))
        user_ids.discard(None)
        if self.inspector:
            user_ids.add(self.inspector.id)
        return User.objects.filter(id__in=user_ids)
    
    parent_inspection = models.ForeignKey(
        'self', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='follow_ups',
        verbose_name="Inspección de Origen"
    )

    def get_total_follow_ups_count(self):
        """
        Cuenta recursivamente TODOS los seguimientos asociados a esta inspección.
        Incluye hijos directos, nietos, bisnietos, etc.
        """
        count = 0
        for child in self.follow_ups.all():
            count += 1  # Contar el hijo directo
            count += child.get_total_follow_ups_count()  # Contar sus descendientes
        return count

    @property
    def get_detail_url(self):
        from django.urls import reverse
        return reverse('first_aid_detail', args=[self.pk])

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
    registered_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Registrado por")

    evidences = GenericRelation('InspectionEvidence')

class FirstAidSignature(models.Model):
    inspection = models.ForeignKey(FirstAidInspection, related_name='signatures', on_delete=models.CASCADE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, verbose_name="Firmante")
    signature = models.TextField(verbose_name="Firma Base64 (Snapshot)")
    signed_at = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de Firma")

    class Meta:
        verbose_name = "Firma de Inspección de Botiquín"
        verbose_name_plural = "Firmas de Inspección de Botiquines"
        unique_together = ('inspection', 'user')

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

    @property
    def get_detail_url(self):
        from django.urls import reverse
        return reverse('process_detail', args=[self.pk])

    class Meta(BaseInspection.Meta):
        verbose_name = "Inspección de Procesos"
        verbose_name_plural = "Inspecciones de Procesos"

    # New fields for standardized logic
    STATUS_CHOICES = [
        ('Programada', 'Programada'),
        ('En proceso', 'En proceso'),
        ('Seguimiento en proceso', 'Seguimiento en proceso'),
        ('Cerrada', 'Cerrada'),
        ('Cerrada con seguimientos', 'Cerrada con seguimientos'),
    ]
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='Programada', verbose_name="Estado")

    def get_participants(self):
        from django.contrib.auth import get_user_model
        User = get_user_model()
        user_ids = set(self.items.values_list('registered_by', flat=True))
        user_ids.discard(None)
        if self.inspector:
            user_ids.add(self.inspector.id)
        return User.objects.filter(id__in=user_ids)
    additional_observations = models.TextField(blank=True, null=True, verbose_name="Observaciones Adicionales")
    parent_inspection = models.ForeignKey(
        'self', 
        on_delete=models.CASCADE, 
        null=True, 
        blank=True, 
        related_name='follow_ups',
        verbose_name="Inspección Padre"
    )

    def get_total_follow_ups_count(self):
        """
        Cuenta recursivamente TODOS los seguimientos asociados a esta inspección.
        Incluye hijos directos, nietos, bisnietos, etc.
        """
        count = 0
        for child in self.follow_ups.all():
            count += 1  # Contar el hijo directo
            count += child.get_total_follow_ups_count()  # Contar sus descendientes
        return count

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
    response = models.CharField(max_length=10, choices=RESPONSE_CHOICES, default='No', verbose_name="Cumple")
    item_status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Bueno', verbose_name="Estado")
    observations = models.CharField(max_length=255, blank=True, verbose_name="Observaciones")
    registered_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Registrado por")

    evidences = GenericRelation('InspectionEvidence')

class ProcessSignature(models.Model):
    inspection = models.ForeignKey(ProcessInspection, related_name='signatures', on_delete=models.CASCADE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, verbose_name="Firmante")
    signature = models.TextField(verbose_name="Firma Base64 (Snapshot)")
    signed_at = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de Firma")

    class Meta:
        verbose_name = "Firma de Inspección de Procesos"
        verbose_name_plural = "Firmas de Inspección de Procesos"
        unique_together = ('inspection', 'user')

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

    @property
    def get_detail_url(self):
        from django.urls import reverse
        return reverse('storage_detail', args=[self.pk])

    class Meta(BaseInspection.Meta):
        verbose_name = "Inspección de Almacenamiento"
        verbose_name_plural = "Inspecciones de Almacenamiento"

    # Standardized logic matching ProcessInspection
    STATUS_CHOICES = [
        ('Programada', 'Programada'),
        ('En proceso', 'En proceso'),
        ('Seguimiento en proceso', 'Seguimiento en proceso'),
        ('Cerrada', 'Cerrada'),
        ('Cerrada con seguimientos', 'Cerrada con seguimientos'),
    ]
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='Programada', verbose_name="Estado")

    def get_participants(self):
        from django.contrib.auth import get_user_model
        User = get_user_model()
        user_ids = set(self.items.values_list('registered_by', flat=True))
        user_ids.discard(None)
        if self.inspector:
            user_ids.add(self.inspector.id)
        return User.objects.filter(id__in=user_ids)
    additional_observations = models.TextField(blank=True, null=True, verbose_name="Observaciones Adicionales")
    parent_inspection = models.ForeignKey(
        'self', 
        on_delete=models.CASCADE, 
        null=True, 
        blank=True, 
        related_name='follow_ups',
        verbose_name="Inspección Padre"
    )

    def get_total_follow_ups_count(self):
        """
        Cuenta recursivamente TODOS los seguimientos asociados a esta inspección.
        """
        count = 0
        for child in self.follow_ups.all():
            count += 1
            count += child.get_total_follow_ups_count()
        return count

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
    response = models.CharField(max_length=10, choices=RESPONSE_CHOICES, default='No', verbose_name="Cumple")
    item_status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Bueno', verbose_name="Estado")
    observations = models.CharField(max_length=255, blank=True, verbose_name="Observaciones")
    registered_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Registrado por")

    evidences = GenericRelation('InspectionEvidence')

    class Meta:
        ordering = ['pk']

class StorageSignature(models.Model):
    inspection = models.ForeignKey(StorageInspection, related_name='signatures', on_delete=models.CASCADE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, verbose_name="Firmante")
    signature = models.TextField(verbose_name="Firma Base64 (Snapshot)")
    signed_at = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de Firma")

    class Meta:
        verbose_name = "Firma de Inspección de Almacenamiento"
        verbose_name_plural = "Firmas de Inspección de Almacenamiento"
        unique_together = ('inspection', 'user')

# 5. Forklift Inspection (R-RH-SST-022)
class ForkliftInspection(BaseInspection):
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
    
    FORKLIFT_TYPE_CHOICES = [
        ('Combustible', 'Montacarga de Combustible'),
        ('Electrico', 'Montacarga Eléctrico'),
    ]
    forklift_type = models.CharField(
        max_length=20, 
        choices=FORKLIFT_TYPE_CHOICES, 
        default='Combustible',
        verbose_name="Tipo de Montacarga",
        blank=True,
        null=True
    )

    STATUS_CHOICES = [
        ('Programada', 'Programada'),
        ('En proceso', 'En proceso'),
        ('Seguimiento en proceso', 'Seguimiento en proceso'),
        ('Cerrada', 'Cerrada'),
        ('Cerrada con seguimientos', 'Cerrada con seguimientos'),
    ]
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='Programada', verbose_name="Estado")

    def save(self, *args, **kwargs):
        # Sync forklift type from asset detail if linked
        if self.asset and hasattr(self.asset, 'montacargas_detail'):
            self.forklift_type = self.asset.montacargas_detail.tipo_montacargas
        super().save(*args, **kwargs)

    def get_participants(self):
        from django.contrib.auth import get_user_model
        User = get_user_model()
        user_ids = set(self.items.values_list('registered_by', flat=True))
        user_ids.discard(None)
        if self.inspector:
            user_ids.add(self.inspector.id)
        return User.objects.filter(id__in=user_ids)
    additional_observations = models.TextField(blank=True, null=True, verbose_name="Observaciones Adicionales")
    parent_inspection = models.ForeignKey(
        'self', 
        on_delete=models.CASCADE, 
        null=True, 
        blank=True, 
        related_name='follow_ups',
        verbose_name="Inspección Padre"
    )
    asset = models.ForeignKey(
        'gestion_activos.Asset',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Activo Relacionado",
        help_text="Activo del inventario asociado a esta inspección",
        related_name='forklift_inspections'
    )

    def get_total_follow_ups_count(self):
        count = 0
        for child in self.follow_ups.all():
            count += 1
            count += child.get_total_follow_ups_count()
        return count

    @property
    def get_detail_url(self):
        from django.urls import reverse
        return reverse('forklift_detail', args=[self.pk])

    class Meta(BaseInspection.Meta):
        verbose_name = "Inspección de Montacargas"
        verbose_name_plural = "Inspecciones de Montacargas"


class ForkliftCheckItem(models.Model):
    RESPONSE_CHOICES = [
        ('Si', 'Si'),
        ('No', 'No'),
        ('NA', 'N/A'),
    ]
    STATUS_CHOICES = [
        ('Bueno', 'Bueno'),
        ('Regular', 'Regular'),
        ('Malo', 'Malo'),
        ('NA', 'No Aplica'),
    ]

    inspection = models.ForeignKey(ForkliftInspection, related_name='items', on_delete=models.CASCADE)
    question = models.CharField(max_length=500, verbose_name="Ítem a Evaluar")
    response = models.CharField(max_length=10, choices=RESPONSE_CHOICES, default='Si', verbose_name="Cumple")
    item_status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Bueno', verbose_name="Estado")
    observations = models.CharField(max_length=255, blank=True, verbose_name="Observación")
    registered_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Registrado por")
    
    evidences = GenericRelation('InspectionEvidence')

    class Meta:
        ordering = ['pk']

class ForkliftSignature(models.Model):
    inspection = models.ForeignKey(ForkliftInspection, related_name='signatures', on_delete=models.CASCADE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, verbose_name="Firmante")
    signature = models.TextField(verbose_name="Firma Base64 (Snapshot)")
    signed_at = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de Firma")

    class Meta:
        verbose_name = "Firma de Inspección de Montacargas"
        verbose_name_plural = "Firmas de Inspección de Montacargas"
        unique_together = ('inspection', 'user')
