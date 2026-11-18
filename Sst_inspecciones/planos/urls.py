from django.urls import path
from .views import PlanosView, UbicarActivoView

urlpatterns = [
    path('', PlanosView.as_view(), name='planos_view'),
    path('ubicar/', UbicarActivoView.as_view(), name='planos_ubicar_activo'),
]
