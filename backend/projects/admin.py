from django.contrib import admin

from projects.models import Project, ProjectLocation, ProjectMilestone


class ProjectLocationInline(admin.StackedInline):
    model = ProjectLocation
    extra = 0


class ProjectMilestoneInline(admin.TabularInline):
    model = ProjectMilestone
    extra = 0


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = [
        "code",
        "title_en",
        "local_government",
        "fiscal_year",
        "status",
        "allocated_amount",
        "data_classification",
    ]
    list_filter = ["status", "data_classification", "fiscal_year", "local_government"]
    list_select_related = ["local_government", "fiscal_year"]
    search_fields = ["code", "title_en", "title_np"]
    inlines = [ProjectLocationInline, ProjectMilestoneInline]
