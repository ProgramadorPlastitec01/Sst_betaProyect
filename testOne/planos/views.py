from django.views.generic import TemplateView, View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.conf import settings
from django.db import transaction
import os


# ── Planos disponibles en el sistema ─────────────────────────────────────────
PLANOS_DISPONIBLES = [
    {'id': 'PL1P1', 'label': 'PL1P1'},
    {'id': 'PL1P2', 'label': 'PL1P2'},
    {'id': 'PL2P1', 'label': 'PL2P1'},
    {'id': 'PL2P2', 'label': 'PL2P2'},
    {'id': 'PL2P3', 'label': 'PL2P3'},
]

PLANO_DEFAULT = 'PL2P1'

# Tipos de activos visibles en planos
TIPOS_VISIBLES = ['Extintor', 'Botiquín', 'Montacargas']


def plano_exists(plano_id):
    """Verifica si el archivo SVG del plano existe en static/planos/."""
    svg_path = os.path.join(settings.BASE_DIR, 'static', 'planos', f'{plano_id}.svg')
    return os.path.isfile(svg_path)


def _icono_por_tipo(tipo_nombre):
    """Retorna la clase Font Awesome según el tipo de activo."""
    mapa = {
        'Extintor':    'fas fa-fire-extinguisher',
        'Botiquín':    'fas fa-medkit',
        'Montacargas': 'fas fa-truck-loading',
    }
    return mapa.get(tipo_nombre, 'fas fa-box')


# ── Vista principal ───────────────────────────────────────────────────────────
class PlanosView(LoginRequiredMixin, TemplateView):
    template_name = 'planos/planos_view.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Plano seleccionado
        plano_id = self.request.GET.get('plano', PLANO_DEFAULT).upper()
        ids_validos = [p['id'] for p in PLANOS_DISPONIBLES]
        if plano_id not in ids_validos:
            plano_id = PLANO_DEFAULT

        svg_existe = plano_exists(plano_id)
        svg_url = f"{settings.STATIC_URL}planos/{plano_id}.svg" if svg_existe else None

        # Activos asignados al plano
        activos = self._get_activos_del_plano(plano_id)

        # Ubicaciones persistidas para este plano
        ubicaciones = self._get_ubicaciones(plano_id)

        # Permisos de edición
        user = self.request.user
        puede_editar = user.is_superuser or (
            hasattr(user, 'role') and user.role and user.role.name == 'Administrador'
        )

        context.update({
            'planos_disponibles': PLANOS_DISPONIBLES,
            'plano_seleccionado': plano_id,
            'svg_existe': svg_existe,
            'svg_url': svg_url,
            'activos': activos,
            'ubicaciones': ubicaciones,
            'puede_editar': puede_editar,
        })
        return context

    def _get_fechas_activo(self, asset):
        """Retorna la fecha de ultima inspección / mantenimiento str formated."""
        if hasattr(asset, 'extintor_detail'):
            return asset.extintor_detail.fecha_recarga.strftime('%d/%m/%Y') if getattr(asset.extintor_detail, 'fecha_recarga', None) else 'Sin registro'
        if hasattr(asset, 'montacargas_detail'):
            return asset.montacargas_detail.fecha_ultimo_mantenimiento.strftime('%d/%m/%Y') if getattr(asset.montacargas_detail, 'fecha_ultimo_mantenimiento', None) else 'Sin registro'
        if hasattr(asset, 'botiquin_detail'):
            return asset.botiquin_detail.fecha_ultima_revision.strftime('%d/%m/%Y') if getattr(asset.botiquin_detail, 'fecha_ultima_revision', None) else 'Sin registro'
        return 'Sin registro'

    def _get_activos_del_plano(self, plano_id):
        from gestion_activos.models import Asset, AssetType
        try:
            # Aquí se pueden cargar todos los activos si algún día se hace un buscador global,
            # pero por ahora respetamos el filtro por plano para la lista lateral.
            activos_qs = (
                Asset.objects
                .filter(
                    plano__nombre=plano_id,
                    activo=True,
                    asset_type__name__in=TIPOS_VISIBLES,
                )
                .select_related('asset_type', 'area', 'plano')
                .prefetch_related('extintor_detail', 'montacargas_detail', 'botiquin_detail')
                .order_by('asset_type__name', 'code')
            )
            result = []
            for asset in activos_qs:
                result.append({
                    'codigo':     asset.code,
                    'tipo':       asset.asset_type.name,
                    'area':       asset.area.name if asset.area else '-',
                    'estado':     asset.estado_label,
                    'estado_css': asset.estado_css,
                    'pk':         asset.pk,
                    'icono':      _icono_por_tipo(asset.asset_type.name),
                    'ultima_insp': self._get_fechas_activo(asset),
                    'plano_asignado': asset.plano.nombre if asset.plano else '',
                })
            return result
        except Exception:
            return []

    def _get_ubicaciones(self, plano_id):
        """Retorna ubicaciones activas del plano como lista de dicts para el template."""
        from .models import UbicacionActivo
        try:
            qs = (
                UbicacionActivo.objects
                .filter(
                    plano=plano_id, 
                    estado='Activo',
                    activo__plano__nombre=plano_id  # <--- CORRECCIÓN CRÍTICA: Solo si el activo pertenece a este plano realmente
                )
                .select_related('activo__asset_type', 'activo__area', 'activo__plano')
                .prefetch_related('activo__extintor_detail', 'activo__montacargas_detail', 'activo__botiquin_detail')
            )
            result = []
            for ub in qs:
                asset = ub.activo
                tipo  = asset.asset_type.name if asset.asset_type else 'Otro'
                plano_asignado = asset.plano.nombre if asset.plano else ''
                
                result.append({
                    'pk':    asset.pk,
                    'code':  asset.code,
                    'tipo':  tipo,
                    'icono': _icono_por_tipo(tipo),
                    'x':     float(ub.posicion_x),
                    'y':     float(ub.posicion_y),
                    'plano_asignado': plano_asignado,
                    'estado': asset.estado_label,
                    'ultima_insp': self._get_fechas_activo(asset),
                })
            return result
        except Exception as e:
            print("ERROR _get_ubicaciones:", e)
            return []


# ── API: Guardar / Mover ubicación ───────────────────────────────────────────
class UbicarActivoView(LoginRequiredMixin, View):
    """
    POST /planos/ubicar/
    Body JSON: { activo_pk, plano, x, y }

    Marca la ubicación anterior del activo en ese plano como 'Inactivo'
    y crea una nueva como 'Activo'. Mantiene historial completo.
    """

    def post(self, request, *args, **kwargs):
        import json
        from gestion_activos.models import Asset
        from .models import UbicacionActivo

        # Verificar permisos de edición
        user = request.user
        puede_editar = user.is_superuser or (
            hasattr(user, 'role') and user.role and user.role.name == 'Administrador'
        )
        if not puede_editar:
            return JsonResponse({'error': 'Sin permiso para editar planos.'}, status=403)

        try:
            data = json.loads(request.body)
        except (ValueError, TypeError):
            return JsonResponse({'error': 'JSON inválido.'}, status=400)

        activo_pk = data.get('activo_pk')
        plano     = (data.get('plano') or '').strip().upper()
        x         = data.get('x')
        y         = data.get('y')

        # Validaciones básicas
        if not activo_pk or not plano or x is None or y is None:
            return JsonResponse({'error': 'Faltan campos requeridos: activo_pk, plano, x, y.'}, status=400)

        ids_validos = [p['id'] for p in PLANOS_DISPONIBLES]
        if plano not in ids_validos:
            return JsonResponse({'error': f'Plano "{plano}" no válido.'}, status=400)

        try:
            x = float(x)
            y = float(y)
        except (ValueError, TypeError):
            return JsonResponse({'error': 'Coordenadas inválidas.'}, status=400)

        try:
            asset = Asset.objects.select_related('asset_type').get(pk=activo_pk)
        except Asset.DoesNotExist:
            return JsonResponse({'error': 'Activo no encontrado.'}, status=404)

        with transaction.atomic():
            # Marcar ubicaciones anteriores de este activo en este plano como Inactivo
            UbicacionActivo.objects.filter(
                activo=asset,
                plano=plano,
                estado='Activo',
            ).update(estado='Inactivo')

            # Crear nueva ubicación activa
            nueva = UbicacionActivo.objects.create(
                activo=asset,
                plano=plano,
                posicion_x=round(x, 2),
                posicion_y=round(y, 2),
                estado='Activo',
                usuario=user,
            )

        tipo = asset.asset_type.name if asset.asset_type else 'Otro'
        return JsonResponse({
            'ok':        True,
            'ubicacion': {
                'pk':   asset.pk,
                'code': asset.code,
                'tipo': tipo,
                'icono': _icono_por_tipo(tipo),
                'x':    float(nueva.posicion_x),
                'y':    float(nueva.posicion_y),
                'fecha': nueva.fecha_registro.strftime('%d/%m/%Y %H:%M'),
            }
        })
