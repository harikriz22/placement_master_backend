from django.urls import path
from .views import StudentListCreateAPIView,StudentDetailAPIView,BatchSwitchAPIView,BatchSwitchHistoryAPIView,AllBatchSwitchHistoryAPIView

urlpatterns = [
    path("",StudentListCreateAPIView.as_view(),name="student-list-create"),
    path("<int:pk>/",StudentDetailAPIView.as_view(),name="student-detail"),
    path("<int:pk>/switch-batch/",BatchSwitchAPIView.as_view(),name="student-batch-switch"),
    path("<int:pk>/batch-history/",BatchSwitchHistoryAPIView.as_view(),name="student-batch-history"),
    path("batch-switch-history/", AllBatchSwitchHistoryAPIView.as_view(), name="all-batch-switch-history"),
    
]