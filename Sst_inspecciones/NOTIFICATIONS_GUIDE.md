# Sistema Global de Notificaciones - Toastr

## Descripción
Sistema centralizado de notificaciones tipo toast implementado con Toastr.js para mostrar mensajes de éxito, error, advertencia e información de manera elegante y no intrusiva.

## Características

### ✅ Configuración Global
- **Posición:** Top-right (esquina superior derecha)
- **Barra de progreso:** Activa
- **Cierre automático:** 4 segundos
- **Cierre manual:** Botón X disponible
- **Animaciones:** Suaves (fadeIn/fadeOut)
- **Prevención de duplicados:** Activada

### ✅ Integración Automática
- Captura automática de mensajes de Django (messages framework)
- No requiere código adicional para mostrar mensajes del backend
- Los mensajes se muestran automáticamente al cargar la página

## Uso

### 1. Desde el Backend (Django)

Los mensajes de Django se capturan y muestran automáticamente:

```python
from django.contrib import messages

# En tus views
def my_view(request):
    # Éxito
    messages.success(request, 'Registro guardado exitosamente')
    
    # Error
    messages.error(request, 'Ocurrió un error al procesar la solicitud')
    
    # Advertencia
    messages.warning(request, 'Por favor revise los datos ingresados')
    
    # Información
    messages.info(request, 'Se han cargado 10 registros')
    
    return redirect('some_url')
```

### 2. Desde el Frontend (JavaScript)

Funciones globales disponibles en cualquier template:

```javascript
// Notificación de éxito
showSuccess('Operación completada exitosamente');
showSuccess('Datos guardados', 'Éxito'); // Con título personalizado

// Notificación de error
showError('No se pudo completar la operación');
showError('Falló la conexión', 'Error de Red');

// Notificación de advertencia
showWarning('Por favor complete todos los campos');
showWarning('Datos incompletos', 'Atención');

// Notificación de información
showInfo('Se encontraron 5 registros');
showInfo('Proceso iniciado', 'Información');
```

### 3. Después de Operaciones AJAX

```javascript
// Ejemplo con fetch
fetch('/api/endpoint/', {
    method: 'POST',
    body: JSON.stringify(data)
})
.then(response => response.json())
.then(data => {
    if (data.success) {
        showSuccess('Datos guardados correctamente');
    } else {
        showError('Error al guardar los datos');
    }
})
.catch(error => {
    showError('Error de conexión');
});
```

### 4. Con Confirmaciones

```javascript
// Ejemplo de confirmación antes de eliminar
function deleteRecord(id) {
    if (confirm('¿Está seguro de eliminar este registro?')) {
        // Realizar eliminación
        fetch(`/api/delete/${id}/`, { method: 'DELETE' })
            .then(() => {
                showSuccess('Registro eliminado exitosamente');
                // Actualizar UI
            })
            .catch(() => {
                showError('No se pudo eliminar el registro');
            });
    }
}
```

## Archivos del Sistema

### 1. `static/js/notifications.js`
Archivo centralizado con:
- Configuración global de Toastr
- Funciones helper (showSuccess, showError, etc.)
- Auto-captura de mensajes de Django
- Utilidades adicionales

### 2. `templates/base.html`
Template base modificado con:
- Link a Toastr CSS (CDN)
- Link a jQuery (requerido por Toastr)
- Link a Toastr JS (CDN)
- Link a notifications.js (custom)
- Contenedor oculto para mensajes de Django

## Personalización

### Cambiar Posición
Editar en `static/js/notifications.js`:
```javascript
toastr.options = {
    "positionClass": "toast-top-right", // Cambiar a: toast-top-left, toast-bottom-right, etc.
    // ... resto de opciones
};
```

### Cambiar Duración
```javascript
toastr.options = {
    "timeOut": "4000", // Milisegundos (4000 = 4 segundos)
    // ... resto de opciones
};
```

### Desactivar Cierre Automático
```javascript
toastr.options = {
    "timeOut": "0", // 0 = no se cierra automáticamente
    "extendedTimeOut": "0",
    // ... resto de opciones
};
```

## Mapeo de Niveles Django → Toastr

| Django Level | Toastr Type | Color    |
|-------------|-------------|----------|
| success     | success     | Verde    |
| error       | error       | Rojo     |
| warning     | warning     | Naranja  |
| info        | info        | Azul     |
| danger      | error       | Rojo     |

## Ejemplos de Uso en el Proyecto

### Ejemplo 1: Guardar Inspección
```python
# views.py
class ExtinguisherCreateView(CreateView):
    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, 'Inspección de extintores guardada exitosamente')
        return response
```

### Ejemplo 2: Validación de Formulario
```python
# views.py
def custom_view(request):
    if not request.POST.get('required_field'):
        messages.warning(request, 'El campo requerido no puede estar vacío')
        return redirect('form_page')
    
    # Procesar...
    messages.success(request, 'Formulario procesado correctamente')
    return redirect('success_page')
```

### Ejemplo 3: Manejo de Errores
```python
# views.py
try:
    # Operación que puede fallar
    process_data()
    messages.success(request, 'Datos procesados exitosamente')
except Exception as e:
    messages.error(request, f'Error al procesar datos: {str(e)}')
    return redirect('error_page')
```

## Ventajas del Sistema

✅ **Centralizado:** Una sola configuración para toda la aplicación
✅ **Automático:** Captura mensajes de Django sin código adicional
✅ **Consistente:** Mismo estilo en toda la aplicación
✅ **No intrusivo:** No bloquea la interfaz
✅ **Responsive:** Se adapta a diferentes tamaños de pantalla
✅ **Accesible:** Permite cierre manual y automático
✅ **Extensible:** Fácil de personalizar y extender

## Notas Importantes

1. **jQuery es requerido:** Toastr depende de jQuery, que se carga desde CDN
2. **Orden de scripts:** Mantener el orden: jQuery → Toastr → notifications.js
3. **Mensajes duplicados:** El sistema previene mostrar el mismo mensaje múltiples veces
4. **Performance:** Los mensajes se eliminan del DOM después de mostrarse

## Troubleshooting

### Las notificaciones no aparecen
1. Verificar que jQuery se cargó correctamente (abrir consola del navegador)
2. Verificar que Toastr se cargó correctamente
3. Verificar que notifications.js se cargó sin errores
4. Revisar la consola del navegador para errores de JavaScript

### Los mensajes de Django no se muestran
1. Verificar que el template extiende de `base.html`
2. Verificar que los mensajes se están enviando desde el backend
3. Revisar que los elementos `.django-message` se están generando en el HTML

### Personalización no funciona
1. Asegurarse de editar `static/js/notifications.js`
2. Limpiar caché del navegador (Ctrl + F5)
3. Verificar que no hay errores de sintaxis en JavaScript
