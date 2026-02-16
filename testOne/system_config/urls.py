from django.urls import path
from .views import AdvancedConfigView

urlpatterns = [
    path('', AdvancedConfigView.as_view(), name='advanced_config'),
]
