from django.urls import path

from app import views

urlpatterns = [
    path("api/v1/health/", views.health),
    path(".well-known/jwks.json", views.jwks),
    path("api/v1/verification/start/", views.start),
    path("api/v1/verification/confirm/", views.confirm),
    path("api/v1/verification/exchange/", views.exchange),
]
