from django.contrib import admin
from .models import AssetType, Asset, TipoExtintor, ExtintorDetail, MontacargasDetail, MovimientoActivo

@admin.register(AssetType)
class AssetTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')

@admin.register(Asset)
class AssetAdmin(admin.ModelAdmin):
    list_display = ('code', 'asset_type', 'area', 'activo', 'temporal', 'estado_actual')
    list_filter = ('activo', 'temporal', 'asset_type', 'area')
    search_fields = ('code',)

@admin.register(TipoExtintor)
class TipoExtintorAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'activo')

@admin.register(ExtintorDetail)
class ExtintorDetailAdmin(admin.ModelAdmin):
    list_display = ('asset_code', 'tipo_agente', 'capacidad_kg', 'estado_movimiento')
    
    def asset_code(self, obj):
        return obj.asset.code
    asset_code.short_description = 'Código Activo'

@admin.register(MontacargasDetail)
class MontacargasDetailAdmin(admin.ModelAdmin):
    list_display = ('asset_code', 'marca', 'modelo')
    
    def asset_code(self, obj):
        return obj.asset.code
    asset_code.short_description = 'Código Activo'

@admin.register(MovimientoActivo)
class MovimientoActivoAdmin(admin.ModelAdmin):
    list_display = ('activo', 'tipo_movimiento', 'fecha', 'responsable', 'created_at')
    list_filter = ('tipo_movimiento', 'fecha')
    search_fields = ('activo__code', 'responsable', 'motivo')
