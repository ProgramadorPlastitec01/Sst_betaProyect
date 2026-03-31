from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView, View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy, reverse
from django.shortcuts import get_object_or_404, redirect, render
from django.contrib import messages
from django.db.models import Q
from django.http import JsonResponse

from .models import Asset, AssetType, ExtintorDetail, MontacargasDetail, BotiquinDetail, TipoExtintor
from .forms import AssetForm, ExtintorDetailForm, MontacargasDetailForm, BotiquinDetailForm, AssetTypeForm, TipoExtintorForm
from roles.mixins import RolePermissionRequiredMixin


# ─────────────────────────────────────────────────────────────────────────────
# ASSET TYPE VIEWS (Solo accesibles desde la Configuración - sin menú lateral)
# ─────────────────────────────────────────────────────────────────────────────

class AssetTypeListView(LoginRequiredMixin, ListView):
    """Lista de tipos de activo - acceso solo desde Configuración."""
    model = AssetType
    template_name = 'gestion_activos/asset_type_list.html'
    context_object_name = 'asset_types'

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_staff:
            messages.error(request, 'Acceso restringido a administradores.')
            return redirect('configuration')
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['total'] = AssetType.objects.count()
        return context


class AssetTypeCreateView(LoginRequiredMixin, CreateView):
    model = AssetType
    form_class = AssetTypeForm
    template_name = 'gestion_activos/asset_type_form.html'
    success_url = reverse_lazy('asset_type_list')

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_staff:
            messages.error(request, 'Acceso restringido a administradores.')
            return redirect('configuration')
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        messages.success(self.request, f'Tipo de activo "{form.instance.name}" creado exitosamente.')
        return super().form_valid(form)


class AssetTypeUpdateView(LoginRequiredMixin, UpdateView):
    model = AssetType
    form_class = AssetTypeForm
    template_name = 'gestion_activos/asset_type_form.html'
    success_url = reverse_lazy('asset_type_list')

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_staff:
            messages.error(request, 'Acceso restringido a administradores.')
            return redirect('configuration')
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        messages.success(self.request, f'Tipo de activo "{form.instance.name}" actualizado correctamente.')
        return super().form_valid(form)


class AssetTypeDeleteView(LoginRequiredMixin, DeleteView):
    model = AssetType
    template_name = 'gestion_activos/asset_type_confirm_delete.html'
    success_url = reverse_lazy('asset_type_list')

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_staff:
            messages.error(request, 'Acceso restringido a administradores.')
            return redirect('configuration')
        return super().dispatch(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        obj = self.get_object()
        if obj.assets.exists():
            messages.error(request, f'No se puede eliminar "{obj.name}" porque tiene activos asociados.')
            return redirect('asset_type_list')
        messages.success(request, f'Tipo de activo "{obj.name}" eliminado.')
        return super().delete(request, *args, **kwargs)


# ─────────────────────────────────────────────────────────────────────────────
# ASSET (OPERATIVO) VIEWS
# ─────────────────────────────────────────────────────────────────────────────

class AssetListView(LoginRequiredMixin, RolePermissionRequiredMixin, ListView):
    permission_required = ('assets', 'view')
    model = Asset
    template_name = 'gestion_activos/asset_list.html'
    context_object_name = 'assets'

    def get_queryset(self):
        qs = Asset.objects.select_related('asset_type', 'area', 'plano').all()

        f_type = self.request.GET.get('tipo', '')
        f_area = self.request.GET.get('area', '')
        f_search = self.request.GET.get('search', '')

        if f_type:
            qs = qs.filter(asset_type_id=f_type)
        if f_area:
            qs = qs.filter(area_id=f_area)
        if f_search:
            qs = qs.filter(code__icontains=f_search)

        f_activo = self.request.GET.get('activo', '')
        if f_activo != '':
            qs = qs.filter(activo=(f_activo == '1'))

        # Filtro de estado se aplica en Python (es calculado)
        f_status = self.request.GET.get('estado', '')
        if f_status:
            # Prefetch detail relations for state calculation
            qs = qs.prefetch_related('extintor_detail', 'montacargas_detail', 'botiquin_detail', 'first_aid_inspections')
            qs = [a for a in qs if a.estado_actual == f_status]
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['asset_types'] = AssetType.objects.all()
        from inspections.models import Area
        context['areas'] = Area.objects.filter(is_active=True)
        context['f_tipo'] = self.request.GET.get('tipo', '')
        context['f_area'] = self.request.GET.get('area', '')
        context['f_search'] = self.request.GET.get('search', '')
        context['f_estado'] = self.request.GET.get('estado', '')

        # Stats
        all_assets = Asset.objects.select_related(
            'asset_type', 'area', 'plano'
        ).prefetch_related('extintor_detail', 'montacargas_detail').all()
        context['total_assets'] = all_assets.count()
        context['activos_count'] = sum(
            1 for a in all_assets
            if a.estado_actual in ('ACTIVO', 'OPERATIVO', 'AL_DIA')
        )
        context['alertas_count'] = sum(
            1 for a in all_assets
            if a.estado_actual in ('VENCIDO', 'PROXIMO_A_VENCER',
                                   'MANTENIMIENTO_VENCIDO', 'PROXIMO_MANTENIMIENTO')
        )
        context['temporales_count'] = sum(1 for a in all_assets if getattr(a, 'temporal', False))
        return context


class AssetDetailView(LoginRequiredMixin, RolePermissionRequiredMixin, DetailView):
    permission_required = ('assets', 'view')
    model = Asset
    template_name = 'gestion_activos/asset_detail.html'
    context_object_name = 'asset'

    def get_queryset(self):
        return Asset.objects.select_related(
            'asset_type', 'area', 'plano'
        ).prefetch_related('extintor_detail', 'montacargas_detail')


class AssetCreateView(LoginRequiredMixin, RolePermissionRequiredMixin, View):
    permission_required = ('assets', 'create')
    template_name = 'gestion_activos/asset_form.html'

    def _get_detail_form(self, asset_type_name, post_data=None, instance=None):
        """Retorna el formulario de detalle según el tipo."""
        name_lower = asset_type_name.lower() if asset_type_name else ''
        if 'extintor' in name_lower:
            return ExtintorDetailForm(post_data, instance=instance), 'extintor'
        if 'montacarga' in name_lower:
            return MontacargasDetailForm(post_data, instance=instance), 'montacargas'
        if 'botiqu' in name_lower:
            return BotiquinDetailForm(post_data, instance=instance), 'botiquin'
        return None, None

    def get(self, request):
        asset_form = AssetForm()
        selected_type = request.GET.get('asset_type', '')
        detail_form = None
        detail_type = None
        if selected_type:
            try:
                atype = AssetType.objects.get(pk=selected_type)
                detail_form, detail_type = self._get_detail_form(atype.name)
            except AssetType.DoesNotExist:
                pass
        return render(request, self.template_name, {
            'form': asset_form,
            'detail_form': detail_form,
            'detail_type': detail_type,
            'asset_types': AssetType.objects.all(),
        })

    def post(self, request):
        asset_form = AssetForm(request.POST)
        detail_form = None
        detail_type = None

        # Resolve detail form
        asset_type_id = request.POST.get('asset_type')
        if asset_type_id:
            try:
                atype = AssetType.objects.get(pk=asset_type_id)
                detail_form, detail_type = self._get_detail_form(atype.name, request.POST)
            except AssetType.DoesNotExist:
                pass

        forms_valid = asset_form.is_valid()
        if detail_form:
            forms_valid = forms_valid and detail_form.is_valid()

        if forms_valid:
            asset = asset_form.save()
            if detail_form:
                detail = detail_form.save(commit=False)
                detail.asset = asset
                detail.save()
            messages.success(request, f'Activo "{asset.code}" creado exitosamente.')
            return redirect('asset_detail', pk=asset.pk)

        return render(request, self.template_name, {
            'form': asset_form,
            'detail_form': detail_form,
            'detail_type': detail_type,
            'asset_types': AssetType.objects.all(),
        })


class AssetUpdateView(LoginRequiredMixin, RolePermissionRequiredMixin, View):
    permission_required = ('assets', 'edit')
    template_name = 'gestion_activos/asset_form.html'

    def _get_existing_detail(self, asset):
        if hasattr(asset, 'extintor_detail'):
            return asset.extintor_detail, 'extintor'
        if hasattr(asset, 'montacargas_detail'):
            return asset.montacargas_detail, 'montacargas'
        if hasattr(asset, 'botiquin_detail'):
            return asset.botiquin_detail, 'botiquin'
        return None, None

    def _get_detail_form(self, asset_type_name, post_data=None, instance=None):
        name_lower = asset_type_name.lower() if asset_type_name else ''
        if 'extintor' in name_lower:
            return ExtintorDetailForm(post_data, instance=instance), 'extintor'
        if 'montacarga' in name_lower:
            return MontacargasDetailForm(post_data, instance=instance), 'montacargas'
        if 'botiqu' in name_lower:
            return BotiquinDetailForm(post_data, instance=instance), 'botiquin'
        return None, None

    def get(self, request, pk):
        asset = get_object_or_404(Asset, pk=pk)
        asset_form = AssetForm(instance=asset)
        existing_detail, detail_type = self._get_existing_detail(asset)
        detail_form, _ = self._get_detail_form(
            asset.asset_type.name if asset.asset_type else '',
            instance=existing_detail
        )
        return render(request, self.template_name, {
            'form': asset_form,
            'detail_form': detail_form,
            'detail_type': detail_type,
            'asset': asset,
            'asset_types': AssetType.objects.all(),
        })

    def post(self, request, pk):
        asset = get_object_or_404(Asset, pk=pk)
        asset_form = AssetForm(request.POST, instance=asset)
        existing_detail, detail_type = self._get_existing_detail(asset)
        detail_form, _ = self._get_detail_form(
            asset.asset_type.name if asset.asset_type else '',
            post_data=request.POST,
            instance=existing_detail
        )

        forms_valid = asset_form.is_valid()
        if detail_form:
            forms_valid = forms_valid and detail_form.is_valid()

        if forms_valid:
            asset = asset_form.save()
            if detail_form:
                detail = detail_form.save(commit=False)
                detail.asset = asset
                detail.save()
            messages.success(request, f'Activo "{asset.code}" actualizado correctamente.')
            return redirect('asset_detail', pk=asset.pk)

        return render(request, self.template_name, {
            'form': asset_form,
            'detail_form': detail_form,
            'detail_type': detail_type,
            'asset': asset,
            'asset_types': AssetType.objects.all(),
        })


class AssetDeleteView(LoginRequiredMixin, RolePermissionRequiredMixin, DeleteView):
    permission_required = ('assets', 'delete')
    model = Asset
    template_name = 'gestion_activos/asset_confirm_delete.html'
    success_url = reverse_lazy('asset_list')

    def delete(self, request, *args, **kwargs):
        asset = self.get_object()
        messages.success(request, f'Activo "{asset.code}" eliminado exitosamente.')
        return super().delete(request, *args, **kwargs)


class AssetTypeDetailFormView(LoginRequiredMixin, View):
    """
    AJAX: devuelve el HTML del formulario de detalle según el tipo seleccionado.
    """
    def get(self, request):
        asset_type_id = request.GET.get('asset_type_id', '')
        if not asset_type_id:
            return JsonResponse({'html': ''})
        try:
            atype = AssetType.objects.get(pk=asset_type_id)
        except AssetType.DoesNotExist:
            return JsonResponse({'html': ''})

        name_lower = atype.name.lower()
        if 'extintor' in name_lower:
            form = ExtintorDetailForm()
            detail_type = 'extintor'
        elif 'montacarga' in name_lower:
            form = MontacargasDetailForm()
            detail_type = 'montacargas'
        elif 'botiqu' in name_lower:
            form = BotiquinDetailForm()
            detail_type = 'botiquin'
        else:
            return JsonResponse({'html': ''})

        html = render(request, 'gestion_activos/_detail_form_partial.html', {
            'detail_form': form,
            'detail_type': detail_type,
        }).content.decode('utf-8')
        return JsonResponse({'html': html})


# ─────────────────────────────────────────────────────────────────────────────
# TIPO EXTINTOR VIEWS (Solo desde Configuración - staff only)
# ─────────────────────────────────────────────────────────────────────────────

class TipoExtintorListView(LoginRequiredMixin, ListView):
    model = TipoExtintor
    template_name = 'gestion_activos/tipo_extintor_list.html'
    context_object_name = 'tipos'

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_staff:
            messages.error(request, 'Acceso restringido a administradores.')
            return redirect('configuration')
        return super().dispatch(request, *args, **kwargs)


class TipoExtintorCreateView(LoginRequiredMixin, CreateView):
    model = TipoExtintor
    form_class = TipoExtintorForm
    template_name = 'gestion_activos/tipo_extintor_form.html'
    success_url = reverse_lazy('tipo_extintor_list')

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_staff:
            messages.error(request, 'Acceso restringido a administradores.')
            return redirect('configuration')
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        messages.success(self.request, f'Tipo "{form.instance.nombre}" creado exitosamente.')
        return super().form_valid(form)


class TipoExtintorUpdateView(LoginRequiredMixin, UpdateView):
    model = TipoExtintor
    form_class = TipoExtintorForm
    template_name = 'gestion_activos/tipo_extintor_form.html'
    success_url = reverse_lazy('tipo_extintor_list')

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_staff:
            messages.error(request, 'Acceso restringido a administradores.')
            return redirect('configuration')
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        messages.success(self.request, f'Tipo "{form.instance.nombre}" actualizado.')
        return super().form_valid(form)


class TipoExtintorDeleteView(LoginRequiredMixin, DeleteView):
    model = TipoExtintor
    template_name = 'gestion_activos/tipo_extintor_confirm_delete.html'
    success_url = reverse_lazy('tipo_extintor_list')

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_staff:
            messages.error(request, 'Acceso restringido a administradores.')
            return redirect('configuration')
        return super().dispatch(request, *args, **kwargs)



    def delete(self, request, *args, **kwargs):
        obj = self.get_object()
        messages.success(request, f'Tipo "{obj.nombre}" eliminado.')
        return super().delete(request, *args, **kwargs)


# ─────────────────────────────────────────────────────────────────────────────
# HISTORIAL DE INSPECCIONES POR ACTIVO (AJAX)
# ─────────────────────────────────────────────────────────────────────────────

class AssetInspectionHistoryView(LoginRequiredMixin, View):
    """
    Devuelve el historial de inspecciones de un activo como JSON.

    Soporta dos tipos de relación:
    - 'direct': el FK al activo está directamente en el modelo de inspección
    - 'items':  el FK al activo está en el modelo de ítems (inspection.items__asset)

    Agregar nuevos módulos es trivial ampliando INSPECTION_SOURCES.
    """

    # Mapa: (app_label.Model, tipo_relacion, label, url_name)
    # tipo_relacion: 'direct' = inspection.asset | 'items' = inspection.items__asset
    INSPECTION_SOURCES = [
        ('inspections.ExtinguisherInspection', 'items',  'Extintor',    'extinguisher_detail'),
        ('inspections.ForkliftInspection',     'direct', 'Montacargas', 'forklift_detail'),
        ('inspections.FirstAidInspection',     'direct', 'Botiquín',    'first_aid_detail'),
    ]

    def _build_queryset(self, Model, rel_type, asset):
        """Construye el queryset según el tipo de relación."""
        if rel_type == 'direct':
            # El FK está directamente en la inspección
            return Model.objects.filter(asset=asset).select_related('inspector', 'area')
        elif rel_type == 'items':
            # El FK está en los ítems: buscar inspecciones que contengan ese activo
            return Model.objects.filter(items__asset=asset).distinct().select_related('inspector', 'area')
        return Model.objects.none()

    def get(self, request, pk):
        asset = get_object_or_404(Asset, pk=pk)
        records = []

        from django.apps import apps
        from django.urls import reverse

        for model_path, rel_type, tipo_label, detail_url_name in self.INSPECTION_SOURCES:
            try:
                app_label, model_name = model_path.split('.')
                Model = apps.get_model(app_label, model_name)
            except (LookupError, ValueError):
                continue

            qs = self._build_queryset(Model, rel_type, asset).order_by('-inspection_date')

            for insp in qs:
                # Estado
                status_val = getattr(insp, 'status', None) or getattr(insp, 'general_status', '-')

                # Inspector
                inspector_name = '-'
                if insp.inspector:
                    inspector_name = insp.inspector.get_full_name() or insp.inspector.username

                # Observaciones
                obs = getattr(insp, 'observations', '') or getattr(insp, 'additional_observations', '') or ''

                # Indicador de si es seguimiento
                es_seguimiento = getattr(insp, 'parent_inspection_id', None) is not None

                # URL de detalle
                try:
                    detail_url = reverse(detail_url_name, args=[insp.pk])
                except Exception:
                    detail_url = '#'

                # Indicadores adicionales
                extra = []
                if es_seguimiento:
                    extra.append('Seguimiento')
                if hasattr(insp, 'items'):
                    try:
                        items_with_recharge = insp.items.filter(
                            asset=asset,
                            fecha_recarga_realizada__isnull=False
                        ).count()
                        if items_with_recharge:
                            extra.append(f'{items_with_recharge} recarga(s)')
                    except Exception:
                        pass

                records.append({
                    'id': insp.pk,
                    'fecha': insp.inspection_date.strftime('%d/%m/%Y') if insp.inspection_date else '-',
                    'fecha_iso': insp.inspection_date.isoformat() if insp.inspection_date else '',
                    'tipo': tipo_label,
                    'status': status_val,
                    'area': str(insp.area) if insp.area else '-',
                    'inspector': inspector_name,
                    'observaciones': str(obs)[:200] if obs else '',
                    'extras': extra,
                    'url': detail_url,
                })

        # Ordenar más reciente primero
        records.sort(key=lambda r: r['fecha_iso'], reverse=True)

        return JsonResponse({
            'asset_code': asset.code,
            'total': len(records),
            'records': records,
        })


# =============================================================================
# MOVIMIENTOS DE ACTIVOS (EXTINTORES)
# Flujo: Salida + Reemplazo atomico → Retorno
# Permiso requerido: assets / gestionar_movimientos (solo Equipo SST)
# =============================================================================

def _can_gestionar_movimientos(user):
    """Verifica si el usuario tiene permiso de gestionar movimientos."""
    if user.is_staff or user.is_superuser:
        return True
    if hasattr(user, 'has_perm_custom'):
        return user.has_perm_custom('assets', 'gestionar_movimientos')
    return False


class AssetMovimientosView(LoginRequiredMixin, View):
    """
    GET: Retorna el historial de movimientos de un activo como JSON.
    Incluye estado actual, temporal asociado y si puede operar.
    """

    def get(self, request, pk):
        from .models import MovimientoActivo
        asset = get_object_or_404(Asset, pk=pk)
        can_manage = _can_gestionar_movimientos(request.user)

        # Solo para extintores
        es_extintor = hasattr(asset, 'extintor_detail')
        estado_actual = asset.estado_actual if es_extintor else None

        # Temporal asociado si está REEMPLAZADO
        temporal_info = None
        if estado_actual == 'REEMPLAZADO':
            temp = asset.get_temporal_activo()
            if temp:
                temporal_info = {
                    'pk': temp.pk,
                    'code': temp.code,
                    'url': reverse('asset_detail', args=[temp.pk]),
                    'estado': temp.estado_actual,
                }

        # Historial de movimientos
        movimientos = MovimientoActivo.objects.filter(
            activo=asset
        ).select_related('activo_relacionado', 'created_by').order_by('-created_at')

        records = []
        for m in movimientos:
            rel_code = m.activo_relacionado.code if m.activo_relacionado else None
            rel_url = reverse('asset_detail', args=[m.activo_relacionado.pk]) if m.activo_relacionado else None
            records.append({
                'pk': m.pk,
                'tipo': m.get_tipo_movimiento_display(),
                'tipo_key': m.tipo_movimiento,
                'fecha': m.fecha.strftime('%d/%m/%Y'),
                'responsable': m.responsable,
                'motivo': m.motivo,
                'observaciones': m.observaciones,
                'relacionado_code': rel_code,
                'relacionado_url': rel_url,
                'registrado_por': m.created_by.get_full_name() or m.created_by.username if m.created_by else '-',
                'created_at': m.created_at.strftime('%d/%m/%Y %H:%M'),
            })

        # Temporales disponibles para seleccionar al registrar reemplazo
        temporales = []
        if can_manage and not asset.temporal and estado_actual in ('ACTIVO', 'VENCIDO', 'PROXIMO_A_VENCER'):
            qs_temp = Asset.objects.filter(
                temporal=True,
                activo=True,
            ).prefetch_related('extintor_detail').order_by('code')
            for t in qs_temp:
                if hasattr(t, 'extintor_detail') and t.extintor_detail.estado_movimiento == 'NORMAL':
                    temporales.append({'pk': t.pk, 'code': t.code, 'area': str(t.area)})

        # Áreas y Tipos para el formulario de nuevo temporal
        areas_list = []
        tipos_list = []
        if can_manage:
            from inspections.models import Area
            from .models import TipoExtintor
            for a in Area.objects.filter(is_active=True).order_by('name'):
                areas_list.append({'pk': a.pk, 'name': a.name})
            for t in TipoExtintor.objects.filter(activo=True).order_by('nombre'):
                tipos_list.append({'pk': t.pk, 'nombre': t.nombre})

        return JsonResponse({
            'asset_pk': asset.pk,
            'asset_code': asset.code,
            'es_extintor': es_extintor,
            'estado_actual': estado_actual,
            'estado_label': asset.estado_label,
            'es_temporal': asset.temporal,
            'can_manage': can_manage,
            'can_salida': can_manage and not asset.temporal and estado_actual in ('ACTIVO', 'VENCIDO', 'PROXIMO_A_VENCER'),
            'can_retorno': can_manage and estado_actual == 'REEMPLAZADO',
            'temporal_asociado': temporal_info,
            'temporales_disponibles': temporales,
            'areas_disponibles': areas_list,
            'tipos_disponibles': tipos_list,
            'movimientos': records,
            'total': len(records),
        })


class RegistrarSalidaYReemplazoView(LoginRequiredMixin, View):
    """
    POST: Registra salida del original + reemplazo con temporal (flujo atomico).
    Datos POST:
      - fecha_salida, responsable_salida, motivo, observaciones (salida)
      - tipo_temporal: 'existente' | 'nuevo'
      - Si existente: temporal_pk
      - Si nuevo: temp_code, temp_area_id, temp_tipo_id, temp_capacidad, temp_fecha_recarga
    """

    def post(self, request, pk):
        from django.db import transaction
        from .models import MovimientoActivo, ExtintorDetail

        if not _can_gestionar_movimientos(request.user):
            return JsonResponse({'ok': False, 'error': 'No tienes permiso para registrar movimientos.'}, status=403)

        asset = get_object_or_404(Asset, pk=pk)

        if not hasattr(asset, 'extintor_detail'):
            return JsonResponse({'ok': False, 'error': 'Este activo no es un extintor.'}, status=400)

        if asset.temporal:
            return JsonResponse({'ok': False, 'error': 'No se puede registrar salida de un extintor que es de reemplazo temporal.'}, status=400)

        estado = asset.estado_actual
        if estado not in ('ACTIVO', 'VENCIDO', 'PROXIMO_A_VENCER'):
            return JsonResponse({'ok': False, 'error': f'Estado "{asset.estado_label}" no permite registrar salida.'}, status=400)

        # Datos de salida
        fecha_salida_str = request.POST.get('fecha_salida', '').strip()
        responsable_salida = request.POST.get('responsable_salida', '').strip()
        motivo = request.POST.get('motivo', '').strip()
        observaciones_salida = request.POST.get('observaciones_salida', '').strip()
        tipo_temporal = request.POST.get('tipo_temporal', '').strip()

        # Validaciones
        errors = {}
        if not fecha_salida_str:
            errors['fecha_salida'] = 'La fecha de salida es obligatoria.'
        if not responsable_salida:
            errors['responsable_salida'] = 'El responsable es obligatorio.'
        if not motivo:
            errors['motivo'] = 'El motivo es obligatorio.'
        if tipo_temporal not in ('existente', 'nuevo'):
            errors['tipo_temporal'] = 'Debes seleccionar o crear un extintor temporal.'

        if errors:
            return JsonResponse({'ok': False, 'errors': errors}, status=422)

        from datetime import date as _date
        try:
            fecha_salida = _date.fromisoformat(fecha_salida_str)
        except ValueError:
            return JsonResponse({'ok': False, 'errors': {'fecha_salida': 'Formato de fecha invalido.'}}, status=422)

        try:
            with transaction.atomic():
                # === Obtener o crear el temporal ===
                if tipo_temporal == 'existente':
                    temporal_pk = request.POST.get('temporal_pk', '').strip()
                    if not temporal_pk:
                        return JsonResponse({'ok': False, 'errors': {'temporal_pk': 'Selecciona un temporal.'}}, status=422)
                    temporal = get_object_or_404(Asset, pk=temporal_pk, temporal=True, activo=True)
                    if not hasattr(temporal, 'extintor_detail'):
                        return JsonResponse({'ok': False, 'error': 'El temporal no tiene datos de extintor.'}, status=400)
                    if temporal.extintor_detail.estado_movimiento != 'NORMAL':
                        return JsonResponse({'ok': False, 'error': 'El temporal seleccionado no esta disponible.'}, status=400)

                elif tipo_temporal == 'nuevo':
                    temp_code = request.POST.get('temp_code', '').strip()
                    temp_area_id = request.POST.get('temp_area_id', '').strip()
                    temp_tipo_id = request.POST.get('temp_tipo_id', '').strip()
                    temp_capacidad = request.POST.get('temp_capacidad', '').strip()
                    temp_fecha_recarga_str = request.POST.get('temp_fecha_recarga', '').strip()

                    errs_t = {}
                    if not temp_code:
                        errs_t['temp_code'] = 'El codigo del temporal es obligatorio.'
                    if not temp_area_id:
                        errs_t['temp_area_id'] = 'El area del temporal es obligatoria.'
                    if not temp_capacidad:
                        errs_t['temp_capacidad'] = 'La capacidad es obligatoria.'
                    if not temp_fecha_recarga_str:
                        errs_t['temp_fecha_recarga'] = 'La fecha de recarga es obligatoria.'
                    if errs_t:
                        return JsonResponse({'ok': False, 'errors': errs_t}, status=422)

                    if Asset.objects.filter(code=temp_code).exists():
                        return JsonResponse({'ok': False, 'errors': {'temp_code': f'Ya existe un activo con codigo "{temp_code}".'} }, status=422)

                    from inspections.models import Area
                    from dateutil.relativedelta import relativedelta
                    try:
                        temp_fecha_recarga = _date.fromisoformat(temp_fecha_recarga_str)
                    except ValueError:
                        return JsonResponse({'ok': False, 'errors': {'temp_fecha_recarga': 'Fecha invalida.'}}, status=422)

                    area_obj = get_object_or_404(Area, pk=temp_area_id)
                    tipo_extintor_obj = TipoExtintor.objects.filter(pk=temp_tipo_id).first() if temp_tipo_id else None
                    fecha_vencimiento_temp = temp_fecha_recarga + relativedelta(years=1)

                    # Obtener el AssetType de extintor
                    extintor_type = asset.asset_type

                    temporal = Asset.objects.create(
                        code=temp_code,
                        asset_type=extintor_type,
                        area=area_obj,
                        activo=True,
                        temporal=True,
                        observaciones=f'Temporal para reemplazo de {asset.code}'
                    )
                    ExtintorDetail.objects.create(
                        asset=temporal,
                        tipo_agente=tipo_extintor_obj,
                        capacidad_kg=float(temp_capacidad),
                        fecha_recarga=temp_fecha_recarga,
                        fecha_vencimiento=fecha_vencimiento_temp,
                        estado_movimiento='NORMAL',
                    )

                # === Registrar Salida del original ===
                MovimientoActivo.objects.create(
                    activo=asset,
                    tipo_movimiento='salida',
                    activo_relacionado=temporal,
                    fecha=fecha_salida,
                    responsable=responsable_salida,
                    motivo=motivo,
                    observaciones=observaciones_salida,
                    created_by=request.user,
                )

                # === Registrar Reemplazo (vincula temporal al original) ===
                MovimientoActivo.objects.create(
                    activo=temporal,
                    tipo_movimiento='reemplazo',
                    activo_relacionado=asset,
                    fecha=fecha_salida,
                    responsable=responsable_salida,
                    motivo=motivo,
                    observaciones=f'Temporal asignado como reemplazo de: {asset.code}',
                    created_by=request.user,
                )

                # === Cambiar estados ===
                asset.extintor_detail.estado_movimiento = 'REEMPLAZADO'
                asset.extintor_detail.save(update_fields=['estado_movimiento'])

        except Exception as e:
            return JsonResponse({'ok': False, 'error': str(e)}, status=500)

        return JsonResponse({
            'ok': True,
            'mensaje': f'Salida registrada. {asset.code} ahora esta en estado Reemplazado. Temporal: {temporal.code}.',
            'nuevo_estado': 'REEMPLAZADO',
            'temporal_code': temporal.code,
            'redirect_url': reverse('asset_detail', args=[asset.pk]),
        })


class RegistrarRetornoView(LoginRequiredMixin, View):
    """
    POST: Registra el retorno del extintor original.
    - Original vuelve a NORMAL
    - Temporal cambia a FUERA_DE_SERVICIO
    Datos POST: fecha_retorno, responsable_retorno, observaciones_retorno
    """

    def post(self, request, pk):
        from django.db import transaction
        from .models import MovimientoActivo

        if not _can_gestionar_movimientos(request.user):
            return JsonResponse({'ok': False, 'error': 'No tienes permiso para registrar movimientos.'}, status=403)

        asset = get_object_or_404(Asset, pk=pk)

        if not hasattr(asset, 'extintor_detail'):
            return JsonResponse({'ok': False, 'error': 'Este activo no es un extintor.'}, status=400)

        if asset.extintor_detail.estado_movimiento != 'REEMPLAZADO':
            return JsonResponse({'ok': False, 'error': f'El activo no esta en estado Reemplazado (estado actual: {asset.estado_label}).'}, status=400)

        temporal = asset.get_temporal_activo()
        if not temporal:
            return JsonResponse({'ok': False, 'error': 'No se encontro el temporal asociado. Contacta al administrador.'}, status=400)

        # Datos del retorno
        fecha_retorno_str = request.POST.get('fecha_retorno', '').strip()
        responsable_retorno = request.POST.get('responsable_retorno', '').strip()
        observaciones_retorno = request.POST.get('observaciones_retorno', '').strip()

        errors = {}
        if not fecha_retorno_str:
            errors['fecha_retorno'] = 'La fecha de retorno es obligatoria.'
        if not responsable_retorno:
            errors['responsable_retorno'] = 'El responsable es obligatorio.'
        if errors:
            return JsonResponse({'ok': False, 'errors': errors}, status=422)

        from datetime import date as _date
        try:
            fecha_retorno = _date.fromisoformat(fecha_retorno_str)
        except ValueError:
            return JsonResponse({'ok': False, 'errors': {'fecha_retorno': 'Formato de fecha invalido.'}}, status=422)

        try:
            with transaction.atomic():
                # 1) Retornar original a NORMAL
                asset.extintor_detail.estado_movimiento = 'NORMAL'
                asset.extintor_detail.save(update_fields=['estado_movimiento'])

                # 2) Dar de baja al temporal
                if hasattr(temporal, 'extintor_detail'):
                    temporal.extintor_detail.estado_movimiento = 'FUERA_DE_SERVICIO'
                    temporal.extintor_detail.save(update_fields=['estado_movimiento'])

                # 3) Registrar Retorno del original
                MovimientoActivo.objects.create(
                    activo=asset,
                    tipo_movimiento='retorno',
                    activo_relacionado=temporal,
                    fecha=fecha_retorno,
                    responsable=responsable_retorno,
                    motivo='',
                    observaciones=observaciones_retorno,
                    created_by=request.user,
                )

                # 4) Registrar Baja del temporal
                MovimientoActivo.objects.create(
                    activo=temporal,
                    tipo_movimiento='baja_temporal',
                    activo_relacionado=asset,
                    fecha=fecha_retorno,
                    responsable=responsable_retorno,
                    motivo='',
                    observaciones=f'Dado de baja al retornar {asset.code}',
                    created_by=request.user,
                )

        except Exception as e:
            return JsonResponse({'ok': False, 'error': str(e)}, status=500)

        return JsonResponse({
            'ok': True,
            'mensaje': f'Retorno registrado. {asset.code} volvio a estado Activo. {temporal.code} quedo Fuera de servicio.',
            'nuevo_estado': 'ACTIVO',
            'redirect_url': reverse('asset_detail', args=[asset.pk]),
        })


class TemporalesDisponiblesView(LoginRequiredMixin, View):
    """GET: Lista temporales disponibles (sin reemplazos activos) para seleccionar."""

    def get(self, request):
        from .models import ExtintorDetail
        qs = Asset.objects.filter(
            temporal=True,
            activo=True,
        ).prefetch_related('extintor_detail').order_by('code')

        data = []
        for t in qs:
            if hasattr(t, 'extintor_detail') and t.extintor_detail.estado_movimiento == 'NORMAL':
                data.append({
                    'pk': t.pk,
                    'code': t.code,
                    'area': str(t.area),
                    'tipo': str(t.extintor_detail.tipo_agente) if t.extintor_detail.tipo_agente else '-',
                    'capacidad': str(t.extintor_detail.capacidad_kg),
                    'vence': t.extintor_detail.fecha_vencimiento.strftime('%d/%m/%Y'),
                })

        return JsonResponse({'temporales': data})


class AssetInventoryReportView(LoginRequiredMixin, RolePermissionRequiredMixin, View):
    """
    Reporte Ejecutivo de Inventario para Activos.
    Muestra KPIs, Graficos y Tabla filtrable.
    """
    permission_required = ('assets', 'view')

    def get(self, request, *args, **kwargs):
        import json
        from .models import Asset, AssetType
        from inspections.models import Area

        # Filtros
        f_area = request.GET.get('area', '')
        f_tipo = request.GET.get('tipo', '')
        f_estado = request.GET.get('estado', '')
        f_temporal = request.GET.get('temporal', '')

        # Base queryset — incluye botiquin_detail para evitar N+1 queries
        qs = Asset.objects.select_related('asset_type', 'area', 'plano').prefetch_related(
            'extintor_detail', 'montacargas_detail', 'botiquin_detail'
        ).all()

        if f_area:
            qs = qs.filter(area_id=f_area)
        if f_tipo:
            qs = qs.filter(asset_type_id=f_tipo)
        if f_temporal == 'si':
            qs = qs.filter(temporal=True)
        elif f_temporal == 'no':
            qs = qs.filter(temporal=False)
        
        # Evaluar estado dinámico
        assets_list = list(qs)
        if f_estado:
            assets_list = [a for a in assets_list if a.estado_actual == f_estado]

        # KPIs — cada tipo de activo tiene su propio vocabulario de estados
        total_assets = len(assets_list)
        # Activos/Operativos/Al día (estado óptimo por tipo)
        total_activos = sum(1 for a in assets_list if a.estado_actual in (
            'ACTIVO', 'OPERATIVO', 'AL_DIA', 'PROXIMA_REVISION', 'PROXIMO_A_VENCER', 'PROXIMO_MANTENIMIENTO'
        ))
        # Vencidos (estado crítico por tipo)
        total_vencidos = sum(1 for a in assets_list if a.estado_actual in (
            'VENCIDO', 'MANTENIMIENTO_VENCIDO', 'REVISION_VENCIDA'
        ))
        total_reemplazados = sum(1 for a in assets_list if a.estado_actual == 'REEMPLAZADO')
        total_fueraservicio = sum(1 for a in assets_list if a.estado_actual == 'FUERA_DE_SERVICIO')
        total_temporales = sum(1 for a in assets_list if a.temporal)

        # Gráficos Data
        status_counts = {}
        type_counts = {}
        area_counts = {}
        temporal_counts = {'Fijos': 0, 'Temporales': 0}

        for a in assets_list:
            # Estado
            st = a.estado_label
            status_counts[st] = status_counts.get(st, 0) + 1
            
            # Tipo
            tp = a.tipo_nombre or 'Sin Tipo'
            type_counts[tp] = type_counts.get(tp, 0) + 1
            
            # Area
            ar = a.area.name if getattr(a, 'area', None) else 'Sin Área'
            area_counts[ar] = area_counts.get(ar, 0) + 1
            
            # Temporal vs Fijo
            if a.temporal:
                temporal_counts['Temporales'] += 1
            else:
                temporal_counts['Fijos'] += 1

        # Generar JSONs para Chart.js
        chart_status = {'labels': list(status_counts.keys()), 'data': list(status_counts.values())}
        chart_type = {'labels': list(type_counts.keys()), 'data': list(type_counts.values())}
        chart_area = {'labels': list(area_counts.keys()), 'data': list(area_counts.values())}
        chart_temp = {'labels': list(temporal_counts.keys()), 'data': list(temporal_counts.values())}

        # Compliance: activos fijos en estado óptimo vs total fijos elegibles
        ESTADOS_OPTIMOS = ('ACTIVO', 'OPERATIVO', 'AL_DIA', 'PROXIMA_REVISION', 'PROXIMO_A_VENCER', 'PROXIMO_MANTENIMIENTO')
        ESTADOS_EXCLUIDOS = ('FUERA_DE_SERVICIO', 'REEMPLAZADO')
        activos_fijos_optimos = sum(1 for a in assets_list if not a.temporal and a.estado_actual in ESTADOS_OPTIMOS)
        activos_fijos_base = sum(1 for a in assets_list if not a.temporal and a.estado_actual not in ESTADOS_EXCLUIDOS)
        cumplimiento = (activos_fijos_optimos / activos_fijos_base * 100) if activos_fijos_base > 0 else 0

        context = {
            'assets': assets_list,
            'areas': Area.objects.filter(is_active=True).order_by('name'),
            'asset_types': AssetType.objects.all().order_by('name'),
            'kpis': {
                'total': total_assets,
                'activos': total_activos,
                'vencidos': total_vencidos,
                'reemplazados': total_reemplazados,
                'fueraservicio': total_fueraservicio,
                'temporales': total_temporales,
                'cumplimiento': round(float(cumplimiento), 1),
            },
            'charts': {
                'status': json.dumps(chart_status),
                'type': json.dumps(chart_type),
                'area': json.dumps(chart_area),
                'temp': json.dumps(chart_temp)
            }
        }
        
        # Soporte Export PDF simple (vista a print mode) con JS, pero si quieren Excel
        if request.GET.get('export') == 'excel':
            import csv
            from django.http import HttpResponse
            response = HttpResponse(content_type='text/csv; charset=utf-8-sig')
            response['Content-Disposition'] = 'attachment; filename="inventario_activos.csv"'
            writer = csv.writer(response, delimiter=';')
            writer.writerow(['Codigo', 'Tipo', 'Area', 'Estado', 'Temporal', 'Fecha Recarga', 'Prox Recarga'])
            for a in assets_list:
                dt = a.get_detail_data()
                fr = dt.fecha_recarga.strftime('%Y-%m-%d') if dt and getattr(dt, 'fecha_recarga', None) else ''
                fv = dt.fecha_vencimiento.strftime('%Y-%m-%d') if dt and getattr(dt, 'fecha_vencimiento', None) else ''
                writer.writerow([
                    a.code,
                    a.tipo_nombre,
                    a.area.name if getattr(a, 'area', None) else '',
                    a.estado_label,
                    'SI' if a.temporal else 'NO',
                    fr,
                    fv
                ])
            return response

        return render(request, 'gestion_activos/asset_report.html', context)
