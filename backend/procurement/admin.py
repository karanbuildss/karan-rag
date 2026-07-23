from django.contrib import admin

from procurement.models import ContractAward, Contractor, Tender


@admin.register(Contractor)
class ContractorAdmin(admin.ModelAdmin):
    list_display = ["name", "registration_number", "municipality_name", "data_classification"]
    list_filter = ["data_classification"]
    search_fields = ["name", "registration_number"]


@admin.register(Tender)
class TenderAdmin(admin.ModelAdmin):
    list_display = ["reference", "project", "procurement_method", "published_date"]
    list_filter = ["procurement_method", "data_classification"]
    list_select_related = ["project"]
    search_fields = ["reference", "title_en", "title_np", "project__title_en"]


@admin.register(ContractAward)
class ContractAwardAdmin(admin.ModelAdmin):
    list_display = ["award_reference", "tender", "contractor", "contract_amount", "awarded_date"]
    list_filter = ["data_classification"]
    list_select_related = ["tender", "contractor"]
    search_fields = ["award_reference", "contractor__name", "tender__reference"]
