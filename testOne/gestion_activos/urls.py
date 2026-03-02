from django.urls import path
from .views import (
    # Asset Type (Configuración)
    AssetTypeListView, AssetTypeCreateView, AssetTypeUpdateView, AssetTypeDeleteView,
    # Tipo Extintor (Configuración)
    TipoExtintorListView, TipoExtintorCreateView, TipoExtintorUpdateView, TipoExtintorDeleteView,
    # Assets (Operativo)
    AssetListView, AssetCreateView, AssetUpdateView, AssetDeleteView, AssetDetailView,
    # AJAX
    AssetTypeDetailFormView,
)

urlpatterns = [
    # ── Asset Types (Configuración) ──────────────────────────────────────────
    path('tipos/', AssetTypeListView.as_view(), name='asset_type_list'),
    path('tipos/add/', AssetTypeCreateView.as_view(), name='asset_type_create'),
    path('tipos/<int:pk>/edit/', AssetTypeUpdateView.as_view(), name='asset_type_update'),
    path('tipos/<int:pk>/delete/', AssetTypeDeleteView.as_view(), name='asset_type_delete'),

    # ── Tipos de Extintor (Configuración) ────────────────────────────────────
    path('tipos-extintor/', TipoExtintorListView.as_view(), name='tipo_extintor_list'),
    path('tipos-extintor/add/', TipoExtintorCreateView.as_view(), name='tipo_extintor_create'),
    path('tipos-extintor/<int:pk>/edit/', TipoExtintorUpdateView.as_view(), name='tipo_extintor_update'),
    path('tipos-extintor/<int:pk>/delete/', TipoExtintorDeleteView.as_view(), name='tipo_extintor_delete'),

    # ── Assets (Operativo) ───────────────────────────────────────────────────
    path('', AssetListView.as_view(), name='asset_list'),
    path('add/', AssetCreateView.as_view(), name='asset_create'),
    path('<int:pk>/', AssetDetailView.as_view(), name='asset_detail'),
    path('<int:pk>/edit/', AssetUpdateView.as_view(), name='asset_update'),
    path('<int:pk>/delete/', AssetDeleteView.as_view(), name='asset_delete'),

    # ── AJAX ─────────────────────────────────────────────────────────────────
    path('ajax/detail-form/', AssetTypeDetailFormView.as_view(), name='asset_detail_form_ajax'),
]
