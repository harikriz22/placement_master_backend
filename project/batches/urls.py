from django.urls import path
from .views import BatchListCreateAPIView, BatchDetailAPIView,CourseListAPIView,BatchStudentsAPIView

urlpatterns = [
    path("", BatchListCreateAPIView.as_view(), name="batch-list-create"),
    path("<int:pk>/", BatchDetailAPIView.as_view(), name="batch-detail"),
    path("courses/", CourseListAPIView.as_view(), name="course-list"),
    path("<int:pk>/students/",BatchStudentsAPIView.as_view(),name="batch-students"),
    
]