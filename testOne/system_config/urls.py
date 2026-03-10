from django.urls import path
from .views import AdvancedConfigView, PlanoListView, PlanoCreateView, PlanoUpdateView, PlanoDeleteView

urlpatterns = [
    path('', AdvancedConfigView.as_view(), name='advanced_config'),
    path('planos/', PlanoListView.as_view(), name='plano_list'),
    path('planos/nuevo/', PlanoCreateView.as_view(), name='plano_create'),
    path('planos/<int:pk>/editar/', PlanoUpdateView.as_view(), name='plano_update'),
    path('planos/<int:pk>/eliminar/', PlanoDeleteView.as_view(), name='plano_delete'),
]
