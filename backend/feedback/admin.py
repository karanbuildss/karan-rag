from django.contrib import admin

from feedback.models import CitizenFeedback, FeedbackRevision, ModerationRecord

admin.site.register(CitizenFeedback)
admin.site.register(FeedbackRevision)
admin.site.register(ModerationRecord)
