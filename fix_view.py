import os
import re

file_path = r'c:\Users\Programador.ti2\Desktop\Antigravity\testOne\inspections\views.py'

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Define the new get_context_data function body
new_body = """    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        years = InspectionSchedule.objects.values_list('year', flat=True).distinct().order_by('-year')
        context['years'] = [str(y) for y in years]
        context['areas'] = InspectionSchedule.objects.values_list('area', flat=True).distinct().order_by('area')
        context['statuses'] = InspectionSchedule.STATUS_CHOICES
        filtered_qs = self.get_queryset()
        
        model_mapping = {
            'Extintores': ExtinguisherInspection,
            'Botiquines': FirstAidInspection,
            'Instalaciones de Proceso': ProcessInspection,
            'Almacenamiento': StorageInspection,
            'Montacargas': ForkliftInspection,
        }
        
        base_types = ['Extintores', 'Botiquines', 'Instalaciones de Proceso', 'Almacenamiento', 'Montacargas']
        found_types = list(filtered_qs.values_list('inspection_type', flat=True).distinct())
        all_types = sorted(list(set(base_types + found_types)))
        
        matrix = []
        months_range = range(1, 13)
        months_names = ['ENE', 'FEB', 'MAR', 'ABR', 'MAY', 'JUN', 'JUL', 'AGO', 'SEPT', 'OCT', 'NOV', 'DIC']

        selected_year = self.request.GET.get('year', '')
        selected_area = self.request.GET.get('area', '')

        for t in all_types:
            type_qs = filtered_qs.filter(inspection_type=t)
            row_cells = []
            total_p = 0
            total_e = 0
            actual_model = model_mapping.get(t)

            for m in months_range:
                p_count = type_qs.filter(scheduled_date__month=m).count()
                e_count = type_qs.filter(scheduled_date__month=m, status='Realizada').count()
                
                if actual_model:
                    actual_qs = actual_model.objects.filter(inspection_date__month=m)
                    if selected_year: actual_qs = actual_qs.filter(inspection_date__year=selected_year)
                    if selected_area: actual_qs = actual_qs.filter(area=selected_area)
                    unlinked_count = actual_qs.filter(schedule_item__isnull=True).count()
                    e_count += unlinked_count

                total_p += p_count
                total_e += e_count
                
                status_class = 'MISS'
                if p_count > 0 and e_count >= p_count: status_class = 'E'
                elif p_count > 0 and e_count > 0: status_class = 'P+E'
                elif p_count > 0: status_class = 'P'
                elif e_count > 0: status_class = 'E'

                row_cells.append({
                    'p': p_count,
                    'e': e_count,
                    'status': status_class
                })
            
            compliance = (total_e / total_p * 100) if total_p > 0 else (100 if total_e > 0 else 0)
            matrix.append({
                'type': t,
                'cells': row_cells,
                'total_p': total_p,
                'total_e': total_e,
                'compliance': round(compliance, 1)
            })

        context['matrix'] = matrix
        context['months_names'] = months_names
        
        total_scheduled = sum(item['total_p'] for item in matrix)
        total_executed = sum(item['total_e'] for item in matrix)
        context['stats'] = {
            'total': total_scheduled,
            'executed': total_executed,
            'percentage': round((total_executed / total_scheduled * 100) if total_scheduled > 0 else (100 if total_executed > 0 else 0), 1)
        }

        monthly_summary = []
        for m_idx in range(12):
            m_p = sum(item['cells'][m_idx]['p'] for item in matrix)
            m_e = sum(item['cells'][m_idx]['e'] for item in matrix)
            monthly_summary.append({'p': m_p, 'e': m_e})
        context['monthly_summary'] = monthly_summary
        return context"""

# Identify the start and end of the get_context_data method
# Looking for "def get_context_data(self, **kwargs):" until the next "def" or end of class
pattern = re.compile(r'    def get_context_data\(self, \*\*kwargs\):.*?return context', re.DOTALL)

if pattern.search(content):
    new_content = pattern.sub(new_body, content)
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(new_content)
    print("Success")
else:
    # Try another way if the return context is missing or different
    print("Pattern not found")
