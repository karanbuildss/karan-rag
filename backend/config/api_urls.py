from budgets.views import BudgetAllocationViewSet, FiscalYearViewSet, SectorViewSet
from django.urls import path
from documents.views import SourceDocumentViewSet
from geography.views import LocalGovernmentViewSet
from investigator.views import InvestigatorQueryView
from projects.views import ProjectViewSet
from rest_framework.routers import DefaultRouter

router = DefaultRouter()
router.register("local-governments", LocalGovernmentViewSet, basename="local-government")
router.register("fiscal-years", FiscalYearViewSet, basename="fiscal-year")
router.register("sectors", SectorViewSet, basename="sector")
router.register("budget-allocations", BudgetAllocationViewSet, basename="budget-allocation")
router.register("projects", ProjectViewSet, basename="project")
router.register("documents", SourceDocumentViewSet, basename="source-document")

urlpatterns = [
    path("investigator/query/", InvestigatorQueryView.as_view(), name="investigator-query"),
    *router.urls,
]
