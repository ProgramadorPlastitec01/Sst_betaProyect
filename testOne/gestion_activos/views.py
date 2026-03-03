from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView, View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy, reverse
from django.shortcuts import get_object_or_404, redirect, render
from django.contrib import messages
from django.db.models import Q
from django.http import JsonResponse

from .models import Asset, AssetType, ExtintorDetail, MontacargasDetail, TipoExtintor
from .forms import AssetForm, ExtintorDetailForm, MontacargasDetailForm, AssetTypeForm, TipoExtintorForm
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
        qs = Asset.objects.select_related('asset_type', 'area').all()

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
            qs = qs.prefetch_related('extintor_detail', 'montacargas_detail')
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
            'asset_type'
        ).prefetch_related('extintor_detail', 'montacargas_detail').all()
        context['total_assets'] = all_assets.count()
        context['activos_count'] = sum(
            1 for a in all_assets
            if a.estado_actual in ('ACTIVO', 'OPERATIVO')
        )
        context['alertas_count'] = sum(
            1 for a in all_assets
            if a.estado_actual in ('VENCIDO', 'PROXIMO_A_VENCER',
                                   'MANTENIMIENTO_VENCIDO', 'PROXIMO_MANTENIMIENTO')
        )
        return context


class AssetDetailView(LoginRequiredMixin, RolePermissionRequiredMixin, DetailView):
    permission_required = ('assets', 'view')
    model = Asset
    template_name = 'gestion_activos/asset_detail.html'
    context_object_name = 'asset'

    def get_queryset(self):
        return Asset.objects.select_related(
            'asset_type', 'area'
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
        return None, None

    def _get_detail_form(self, asset_type_name, post_data=None, instance=None):
        name_lower = asset_type_name.lower() if asset_type_name else ''
        if 'extintor' in name_lower:
            return ExtintorDetailForm(post_data, instance=instance), 'extintor'
        if 'montacarga' in name_lower:
            return MontacargasDetailForm(post_data, instance=instance), 'montacargas'
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
    Recorre todos los módulos de inspección que tienen FK al activo.
    Escalable: agregar nuevos modelos de inspección es trivial.
    """

    # Mapa de (modelo, campo_FK, tipo_label, url_name)
    INSPECTION_SOURCES = [
        # (app_label.Model, field_on_model, label, detail_url_name)
        ('inspections.ExtinguisherInspection', 'asset', 'Extintor', 'extinguisher_detail'),
        ('inspections.ForkliftInspection',     'asset', 'Montacargas', 'forklift_detail'),
    ]

    def get(self, request, pk):
        asset = get_object_or_404(Asset, pk=pk)
        records = []

        from django.apps import apps

        for model_path, fk_field, tipo_label, detail_url_name in self.INSPECTION_SOURCES:
            try:
                app_label, model_name = model_path.split('.')
                Model = apps.get_model(app_label, model_name)
            except (LookupError, ValueError):
                continue

            qs = Model.objects.filter(
                **{fk_field: asset}
            ).select_related('inspector', 'area').order_by('-inspection_date')

            for insp in qs:
                # Estado
                status_val = getattr(insp, 'status', None) or getattr(insp, 'general_status', '—')

                # Inspector
                inspector_name = '—'
                if insp.inspector:
                    inspector_name = insp.inspector.get_full_name() or insp.inspector.username

                # Observaciones
                obs = getattr(insp, 'observations', '') or getattr(insp, 'additional_observations', '') or ''

                # URL de detalle
                try:
                    from django.urls import reverse
                    detail_url = reverse(detail_url_name, args=[insp.pk])
                except Exception:
                    detail_url = '#'

                # Indicadores adicionales (recarga, etc.)
                extra = []
                if hasattr(insp, 'items'):
                    try:
                        items_with_recharge = insp.items.filter(
                            fecha_recarga_realizada__isnull=False
                        ).count()
                        if items_with_recharge:
                            extra.append(f'{items_with_recharge} recarga(s)')
                    except Exception:
                        pass

                records.append({
                    'id': insp.pk,
                    'fecha': insp.inspection_date.strftime('%d/%m/%Y') if insp.inspection_date else '—',
                    'fecha_iso': insp.inspection_date.isoformat() if insp.inspection_date else '',
                    'tipo': tipo_label,
                    'status': status_val,
                    'area': str(insp.area) if insp.area else '—',
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
