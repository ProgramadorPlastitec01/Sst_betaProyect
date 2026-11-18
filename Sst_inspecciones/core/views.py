from django.views.generic import TemplateView, View
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.http import HttpResponse


class PingView(View):
    """
    Endpoint liviano para el indicador de estado de red (static/js/network_status.js).
    Sin autenticación ni consulta a BD: se llama cada 10-15s desde el cliente.
    """
    def get(self, request):
        response = HttpResponse(status=204)
        response['Cache-Control'] = 'no-store'
        return response


class ConfigurationView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    template_name = 'configuration/index.html'
    
    def test_func(self):
        # Solo usuarios staff pueden acceder
        return self.request.user.is_staff
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Configuración del Sistema'
        return context
