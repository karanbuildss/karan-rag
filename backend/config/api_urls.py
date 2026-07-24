from accounts.views import (
    CompleteVerificationView,
    CsrfTokenView,
    LoginView,
    LogoutView,
    MeView,
    RegisterView,
)
from anomalies.views import AnomalyFlagViewSet
from budgets.views import BudgetAllocationViewSet, FiscalYearViewSet, SectorViewSet
from chat.views import ChatSessionViewSet
from django.urls import path
from documents.views import SourceDocumentViewSet
from feedback.views import CitizenFeedbackViewSet
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
router.register("feedback", CitizenFeedbackViewSet, basename="feedback")
router.register("anomalies", AnomalyFlagViewSet, basename="anomaly")
router.register("chat-sessions", ChatSessionViewSet, basename="chat-session")

urlpatterns = [
    path("auth/csrf/", CsrfTokenView.as_view(), name="auth-csrf"),
    path("auth/register/", RegisterView.as_view(), name="auth-register"),
    path("auth/login/", LoginView.as_view(), name="auth-login"),
    path("auth/logout/", LogoutView.as_view(), name="auth-logout"),
    path("auth/me/", MeView.as_view(), name="auth-me"),
    path(
        "verification/complete/",
        CompleteVerificationView.as_view(),
        name="verification-complete",
    ),
    path("investigator/query/", InvestigatorQueryView.as_view(), name="investigator-query"),
    *router.urls,
]
