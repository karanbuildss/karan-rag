from django.contrib import admin

from geography.models import District, LocalGovernment, Province, Ward


@admin.register(Province)
class ProvinceAdmin(admin.ModelAdmin):
    list_display = ["code", "name_en", "name_np"]
    search_fields = ["code", "name_en", "name_np"]


@admin.register(District)
class DistrictAdmin(admin.ModelAdmin):
    list_display = ["code", "name_en", "province"]
    list_select_related = ["province"]
    search_fields = ["code", "name_en", "name_np"]


@admin.register(LocalGovernment)
class LocalGovernmentAdmin(admin.ModelAdmin):
    list_display = ["code", "name_en", "government_type", "district"]
    list_filter = ["government_type", "district__province"]
    list_select_related = ["district"]
    search_fields = ["code", "name_en", "name_np"]


@admin.register(Ward)
class WardAdmin(admin.ModelAdmin):
    list_display = ["local_government", "number", "name_en"]
    list_filter = ["local_government"]
    list_select_related = ["local_government"]
