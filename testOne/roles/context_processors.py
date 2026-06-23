"""
roles/context_processors.py
----------------------------
Context processor que expone el estado de simulación de roles a todos los templates.

Inyecta la variable `simulated_role` en cada request context:
  - None  → No hay simulación activa (comportamiento normal)
  - Role  → El objeto Role que se está simulando

Esto permite que los templates usen {{ simulated_role }} sin referirse al
atributo privado user._simulated_role (que Django prohíbe en templates).
"""


def role_simulation(request):
    """
    Expone el rol simulado activo al contexto de los templates.
    Si no hay simulación activa devuelve None (evaluación falsy en templates).
    """
    simulated_role = getattr(request.user, '_simulated_role', None) if hasattr(request, 'user') else None
    return {
        'simulated_role': simulated_role,
    }
