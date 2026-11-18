import os

path = r'c:\Users\Programador.ti2\Desktop\Antigravity\testOne\inspections\models.py'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

# Replace strings for Process, Storage, Forklift
new_choices = """    STATUS_CHOICES = [
        ('Programada', 'Programada'),
        ('En proceso', 'En proceso'),
        ('Seguimiento en proceso', 'Seguimiento en proceso'),
        ('Cerrada', 'Cerrada'),
        ('Cerrada con seguimientos', 'Cerrada con seguimientos'),
    ]
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='Programada', verbose_name="Estado")"""

# Target for Process and Storage (they are identical)
target1 = """    STATUS_CHOICES = [
        ('Pendiente', 'Pendiente por ejecutar'),
        ('En proceso', 'En proceso'),
        ('Pendiente de Firmas', 'Pendiente de Firmas'),
        ('Cerrada', 'Cerrada'),
        ('Cerrada con Hallazgos', 'Cerrada con Hallazgos'),
    ]
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='Pendiente', verbose_name="Estado")"""

# Target for Forklift (different spacing/content in Pendiente)
target2 = """    STATUS_CHOICES = [
        ('Pendiente', 'Pendiente'),
        ('En proceso', 'En proceso'),
        ('Pendiente de Firmas', 'Pendiente de Firmas'),
        ('Cerrada', 'Cerrada'),
        ('Cerrada con Hallazgos', 'Cerrada con Hallazgos')
    ]
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='Pendiente', verbose_name="Estado")"""

# Normalize line endings for replacement
content = content.replace(target1, new_choices)
content = content.replace(target2, new_choices)

with open(path, 'w', encoding='utf-8') as f:
    f.write(content)
print("Done")
