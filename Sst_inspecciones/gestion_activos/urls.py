from django.urls import path
from .views import (
    # Asset Type (Configuracion)
    AssetTypeListView, AssetTypeCreateView, AssetTypeUpdateView, AssetTypeDeleteView,
    # Tipo Extintor (Configuracion)
    TipoExtintorListView, TipoExtintorCreateView, TipoExtintorUpdateView, TipoExtintorDeleteView,
    # Assets (Operativo)
    AssetListView, AssetCreateView, AssetUpdateView, AssetDeleteView, AssetDetailView,
    # Historial de Inspecciones
    AssetInspectionHistoryView,
    # Movimientos de Activos
    AssetMovimientosView, RegistrarSalidaYReemplazoView, RegistrarRetornoView, TemporalesDisponiblesView,
    # Reportes
    AssetInventoryReportView,
    # AJAX
    AssetTypeDetailFormView,
)

urlpatterns = [
    # -- Asset Types (Configuracion) -------------------------------------------------------
    path('tipos/', AssetTypeListView.as_view(), name='asset_type_list'),
    path('tipos/add/', AssetTypeCreateView.as_view(), name='asset_type_create'),
    path('tipos/<int:pk>/edit/', AssetTypeUpdateView.as_view(), name='asset_type_update'),
    path('tipos/<int:pk>/delete/', AssetTypeDeleteView.as_view(), name='asset_type_delete'),

    # -- Tipos de Extintor (Configuracion) -------------------------------------------------
    path('tipos-extintor/', TipoExtintorListView.as_view(), name='tipo_extintor_list'),
    path('tipos-extintor/add/', TipoExtintorCreateView.as_view(), name='tipo_extintor_create'),
    path('tipos-extintor/<int:pk>/edit/', TipoExtintorUpdateView.as_view(), name='tipo_extintor_update'),
    path('tipos-extintor/<int:pk>/delete/', TipoExtintorDeleteView.as_view(), name='tipo_extintor_delete'),

    # -- Assets (Operativo) ----------------------------------------------------------------
    path('', AssetListView.as_view(), name='asset_list'),
    path('add/', AssetCreateView.as_view(), name='asset_create'),
    path('<int:pk>/', AssetDetailView.as_view(), name='asset_detail'),
    path('<int:pk>/edit/', AssetUpdateView.as_view(), name='asset_update'),
    path('<int:pk>/delete/', AssetDeleteView.as_view(), name='asset_delete'),
    path('<int:pk>/historial-inspecciones/', AssetInspectionHistoryView.as_view(), name='asset_inspection_history'),

    # -- Movimientos de Activos ------------------------------------------------------------
    path('<int:pk>/movimientos/', AssetMovimientosView.as_view(), name='asset_movimientos'),
    path('<int:pk>/movimientos/salida/', RegistrarSalidaYReemplazoView.as_view(), name='asset_registrar_salida'),
    path('<int:pk>/movimientos/retorno/', RegistrarRetornoView.as_view(), name='asset_registrar_retorno'),
    path('temporales-disponibles/', TemporalesDisponiblesView.as_view(), name='asset_temporales_disponibles'),

    # -- Reportes --------------------------------------------------------------------------
    path('reporte/', AssetInventoryReportView.as_view(), name='asset_report'),

    # -- AJAX ------------------------------------------------------------------------------
    path('ajax/detail-form/', AssetTypeDetailFormView.as_view(), name='asset_detail_form_ajax'),
]
