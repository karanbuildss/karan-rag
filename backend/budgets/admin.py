from django.contrib import admin

from budgets.models import BudgetAllocation, FiscalYear, Sector, SubSector

admin.site.register(FiscalYear)
admin.site.register(Sector)
admin.site.register(SubSector)


@admin.register(BudgetAllocation)
class BudgetAllocationAdmin(admin.ModelAdmin):
    list_display = [
        "local_government",
        "fiscal_year",
        "subsector",
        "budget_type",
        "allocated_amount",
        "spent_amount",
        "data_classification",
    ]
    list_filter = ["budget_type", "data_classification", "fiscal_year"]
    list_select_related = ["local_government", "fiscal_year", "subsector"]
    search_fields = ["local_government__name_en", "subsector__name_en"]
