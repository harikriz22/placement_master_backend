from django.urls import path
from . import views

urlpatterns = [
    path("preview/", views.StudentImportPreviewView.as_view(), name="student-import-preview"),
    path("confirm/",views.StudentImportConfirmView.as_view(),name="student-import-confirm"),
]