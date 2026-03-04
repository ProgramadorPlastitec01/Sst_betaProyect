import os
import re

templates_dir = r'c:\Users\Programador.ti2\Desktop\Antigravity\testOne\templates\inspections'
files = [f for f in os.listdir(templates_dir) if f.endswith('_detail.html')]

badge_pattern = r'class="badge \{% if object\.status == \'Cerrada\' %\}.*?\{% endif %\}"'
badge_replacement = 'class="badge {% if object.status == \'Cerrada\' or object.status == \'Cerrada con seguimientos\' %}badge-success{% elif object.status == \'Seguimiento en proceso\' %}badge-orange{% elif object.status == \'En proceso\' %}badge-primary{% elif object.status == \'Programada\' %}badge-secondary{% else %}badge-secondary{% endif %}"'

edit_button_pattern = r'\{% if object\.status != \'Cerrada\' and object\.status != \'Cerrada con Hallazgos\' %\}'
edit_button_replacement = '{% if object.status != \'Cerrada\' and object.status != \'Cerrada con seguimientos\' %}'

for filename in files:
    path = os.path.join(templates_dir, filename)
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Update badges
    content = re.sub(badge_pattern, badge_replacement, content)
    
    # Update edit button logic
    content = re.sub(edit_button_pattern, edit_button_replacement, content)
    
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)

print("Modified templates:", files)
