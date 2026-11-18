import os
import re

templates_dir = r'c:\Users\Programador.ti2\Desktop\Antigravity\testOne\templates\inspections'
files = [f for f in os.listdir(templates_dir) if f.endswith('_list.html')]

# 1. Update status badge colors and logic
status_block_pattern = r'\{% if inspection\.status == \'Cerrada\' %\}.*?\{% endif %\}'
status_block_replacement = """{% if inspection.status == 'Cerrada' or inspection.status == 'Cerrada con seguimientos' %}
                                    background: #d4edda; color: #155724;
                                {% elif inspection.status == 'Seguimiento en proceso' or inspection.status == 'Cerrada con Hallazgos' %}
                                    background: #ffe4cc; color: #e67e22;
                                {% elif inspection.status == 'En proceso' or inspection.status == 'Pendiente de Firmas' %}
                                    background: #cce5ff; color: #004085;
                                {% else %}
                                    background: #e2e3e5; color: #495057;
                                {% endif %}"""

# 2. Update status icons
icon_block_pattern = r'\{% if inspection\.status == \'Pendiente de Firmas\' %\}.*?\{% endif %\}'
icon_block_replacement = """{% if inspection.status == 'Cerrada' or inspection.status == 'Cerrada con seguimientos' %}
                                <i class="fas fa-check-circle" style="margin-right:4px;"></i>
                                {% elif inspection.status == 'Seguimiento en proceso' or inspection.status == 'Cerrada con Hallazgos' %}
                                <i class="fas fa-exclamation-circle" style="margin-right:4px;"></i>
                                {% elif inspection.status == 'En proceso' or inspection.status == 'Pendiente de Firmas' %}
                                <i class="fas fa-spinner" style="margin-right:4px;"></i>
                                {% else %}
                                <i class="fas fa-clock" style="margin-right:4px;"></i>
                                {% endif %}"""

# 3. Update edit button logic
edit_btn_pattern = r'\{% if inspection\.status != \'Cerrada\' and inspection\.status != \'Cerrada con Hallazgos\' %\}'
edit_btn_replacement = "{% if inspection.status != 'Cerrada' and inspection.status != 'Cerrada con seguimientos' %}"

for filename in files:
    path = os.path.join(templates_dir, filename)
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # We use re.DOTALL to match across multiple lines
    content = re.sub(status_block_pattern, status_block_replacement, content, flags=re.DOTALL)
    content = re.sub(icon_block_pattern, icon_block_replacement, content, flags=re.DOTALL)
    content = re.sub(edit_btn_pattern, edit_btn_replacement, content)
    
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)

print("Modified list templates:", files)
