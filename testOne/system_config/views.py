from django.shortcuts import render, redirect
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views import View
from django.contrib import messages
from .models import SystemConfig

class AdvancedConfigView(LoginRequiredMixin, View):
    template_name = 'system_config/advanced_settings.html'

    def get(self, request):
        # We need to ensure only staff/admin access usually, but per requirement "integrate as other options"
        # Assuming staff access required as per general config view.
        if not request.user.is_staff:
             messages.error(request, "No tienes permisos para acceder a esta configuración.")
             return redirect('dashboard')

        configs = SystemConfig.objects.all().order_by('category', 'key')
        grouped_configs = {}
        for config in configs:
            if config.category not in grouped_configs:
                grouped_configs[config.category] = []
            grouped_configs[config.category].append(config)
        
        return render(request, self.template_name, {'grouped_configs': grouped_configs})

    def post(self, request):
        if not request.user.is_staff:
             messages.error(request, "No tienes permisos para realizar cambios.")
             return redirect('dashboard')

        configs = SystemConfig.objects.filter(is_editable=True)
        changed = False
        errors = False
        
        for config in configs:
            field_name = f'config_{config.id}'
            
            if config.config_type == 'boolean':
                # Checkbox handling: presence means True, absence means False
                new_value = 'true' if field_name in request.POST else 'false'
                if new_value != config.value:
                    config.value = new_value
                    config.save()
                    changed = True
            
            elif field_name in request.POST:
                new_value = request.POST[field_name]
                
                if config.config_type == 'number':
                    try:
                        val = float(new_value)
                        if val < 0:
                            messages.error(request, f"El valor para '{config.description}' no puede ser negativo.")
                            errors = True
                            continue
                        
                        # Store as integer if it's a whole number for cleaner display
                        clean_val = str(int(val)) if val.is_integer() else str(val)
                        
                        if clean_val != config.value:
                            config.value = clean_val
                            config.save()
                            changed = True
                    except ValueError:
                         messages.error(request, f"El valor para '{config.description}' debe ser numérico.")
                         errors = True
                else:
                    if new_value != config.value:
                        config.value = new_value
                        config.save()
                        changed = True

        if changed and not errors:
            messages.success(request, "Configuración actualizada correctamente.")
        elif not changed and not errors:
            messages.info(request, "No se realizaron cambios.")
            
        return redirect('advanced_config')
