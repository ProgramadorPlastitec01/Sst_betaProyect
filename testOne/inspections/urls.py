from django.urls import path
from .views import (
    InspectionListView, InspectionCreateView, 
    InspectionUpdateView, InspectionDeleteView,
    
    # New Views
    # New Views
    ExtinguisherListView, ExtinguisherCreateView, ExtinguisherUpdateView, ExtinguisherDetailView, 
    SignExtinguisherInspectionView, ExtinguisherReportView,
    ExtinguisherItemCreateView, ExtinguisherItemUpdateView,
    FirstAidListView, FirstAidCreateView, FirstAidUpdateView, FirstAidDetailView,
    SignFirstAidInspectionView, FirstAidReportView,
    FirstAidItemCreateView, FirstAidItemUpdateView,
    ProcessListView, ProcessCreateView, ProcessUpdateView, ProcessDetailView,
    SignProcessInspectionView, ProcessReportView,
    StorageListView, StorageCreateView, StorageUpdateView, StorageDetailView,
    
    # Forklift Views
    ForkliftListView, ForkliftCreateView, ForkliftUpdateView, ForkliftDetailView
)

# Area Management Views
from .area_views import AreaListView, AreaCreateView, AreaUpdateView

urlpatterns = [
    # Existing Schedule
    path('', InspectionListView.as_view(), name='inspection_list'),
    path('schedule/create/', InspectionCreateView.as_view(), name='inspection_create'), # Renamed slightly to avoid confusion? No, keep existing pattern but maybe prefix 'schedule/'
    path('schedule/<int:pk>/edit/', InspectionUpdateView.as_view(), name='inspection_edit'),
    path('schedule/<int:pk>/delete/', InspectionDeleteView.as_view(), name='inspection_delete'),

    # 1. Extinguishers
    path('extinguishers/', ExtinguisherListView.as_view(), name='extinguisher_list'),
    path('extinguishers/add/', ExtinguisherCreateView.as_view(), name='extinguisher_create'),
    path('extinguishers/<int:pk>/', ExtinguisherDetailView.as_view(), name='extinguisher_detail'),
    path('extinguishers/<int:pk>/edit/', ExtinguisherUpdateView.as_view(), name='extinguisher_edit'),
    path('extinguishers/<int:pk>/sign/', SignExtinguisherInspectionView.as_view(), name='extinguisher_sign'),
    path('extinguishers/<int:pk>/report/', ExtinguisherReportView.as_view(), name='extinguisher_report'),
    
    # Items
    path('extinguishers/<int:pk>/add-item/', ExtinguisherItemCreateView.as_view(), name='extinguisher_item_create'),
    path('extinguishers/item/<int:pk>/edit/', ExtinguisherItemUpdateView.as_view(), name='extinguisher_item_edit'),

    # 2. First Aid
    path('first-aid/', FirstAidListView.as_view(), name='first_aid_list'),
    path('first-aid/add/', FirstAidCreateView.as_view(), name='first_aid_create'),
    path('first-aid/<int:pk>/', FirstAidDetailView.as_view(), name='first_aid_detail'),
    path('first-aid/<int:pk>/edit/', FirstAidUpdateView.as_view(), name='first_aid_edit'),
    path('first-aid/<int:pk>/sign/', SignFirstAidInspectionView.as_view(), name='first_aid_sign'),
    path('first-aid/<int:pk>/report/', FirstAidReportView.as_view(), name='first_aid_report'),

    # Items
    path('first-aid/<int:pk>/add-item/', FirstAidItemCreateView.as_view(), name='first_aid_item_create'),
    path('first-aid/item/<int:pk>/edit/', FirstAidItemUpdateView.as_view(), name='first_aid_item_edit'),

    # 3. Process Checklists
    path('process/', ProcessListView.as_view(), name='process_list'),
    path('process/add/', ProcessCreateView.as_view(), name='process_create'),
    path('process/<int:pk>/', ProcessDetailView.as_view(), name='process_detail'),
    path('process/<int:pk>/edit/', ProcessUpdateView.as_view(), name='process_edit'),
    path('process/<int:pk>/sign/', SignProcessInspectionView.as_view(), name='sign_process_inspection'),
    path('process/<int:pk>/report/', ProcessReportView.as_view(), name='process_report'),

    # 4. Storage Checklists
    path('storage/', StorageListView.as_view(), name='storage_list'),
    path('storage/add/', StorageCreateView.as_view(), name='storage_create'),
    path('storage/<int:pk>/', StorageDetailView.as_view(), name='storage_detail'),
    path('storage/<int:pk>/edit/', StorageUpdateView.as_view(), name='storage_edit'),

    # 5. Forklift Checklists
    path('forklift/', ForkliftListView.as_view(), name='forklift_list'),
    path('forklift/add/', ForkliftCreateView.as_view(), name='forklift_create'),
    path('forklift/<int:pk>/', ForkliftDetailView.as_view(), name='forklift_detail'),
    path('forklift/<int:pk>/edit/', ForkliftUpdateView.as_view(), name='forklift_edit'),
    
    # 6. Area Management
    path('areas/', AreaListView.as_view(), name='area_list'),
    path('areas/add/', AreaCreateView.as_view(), name='area_create'),
    path('areas/<int:pk>/edit/', AreaUpdateView.as_view(), name='area_update'),
]
