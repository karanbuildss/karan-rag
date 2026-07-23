from django.contrib import admin

from payments.models import Payment


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ["reference", "contract_award", "amount", "paid_on", "data_classification"]
    list_filter = ["data_classification", "paid_on"]
    list_select_related = ["contract_award", "milestone"]
    search_fields = ["reference", "contract_award__award_reference"]
