import os
import re

path = r'c:\Users\Programador.ti2\Desktop\Antigravity\testOne\inspections\views.py'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

# Define classes and their form_valid replacements
classes_to_fix = [
    'ExtinguisherCreateView',
    'ExtinguisherUpdateView',
    'FirstAidCreateView',
    'FirstAidUpdateView',
    'ProcessCreateView',
    'ProcessUpdateView',
    'StorageCreateView',
    'StorageUpdateView',
    'ForkliftCreateView',
    'ForkliftUpdateView',
]

for cls_name in classes_to_fix:
    # Find the class block and its form_valid method
    pattern = rf"(class {cls_name}\(.*?def form_valid\(self, form\):.*?)(response = super\(\)\.form_valid\(form\))"
    replacement = r"\1if form.instance.status == 'Programada':\n            form.instance.status = 'En proceso'\n        \2"
    content = re.sub(pattern, replacement, content, flags=re.DOTALL)

with open(path, 'w', encoding='utf-8') as f:
    f.write(content)
print("Done")
