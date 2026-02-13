from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin

class ConfigurationView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    template_name = 'configuration/index.html'
    
    def test_func(self):
        # Solo usuarios staff pueden acceder
        return self.request.user.is_staff
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Configuración del Sistema'
        return context
