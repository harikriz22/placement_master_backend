from django.urls import path
from .views import BatchListCreateAPIView, BatchDetailAPIView

urlpatterns = [
    path("", BatchListCreateAPIView.as_view(), name="batch-list-create"),
    path("<int:pk>/", BatchDetailAPIView.as_view(), name="batch-detail"),
]