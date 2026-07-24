from django.contrib import admin

from accounts.models import CitizenProfile, VerificationRecord

admin.site.register(CitizenProfile)
admin.site.register(VerificationRecord)
