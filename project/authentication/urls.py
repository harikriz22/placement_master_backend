from django.urls import path

from .views import MemberRegistrationAPIView,LoginAPIView,LogoutAPIView,RefreshTokenAPIView,CurrentMemberAPIView


urlpatterns = [
    path("register/",MemberRegistrationAPIView.as_view(),name="member-register"),
    path("login/",LoginAPIView.as_view(),name="member-login"),
    path("logout/",LogoutAPIView.as_view(),name="member-logout"),
    path("refresh/",RefreshTokenAPIView.as_view(),name="refresh-token"),
    path("me/", CurrentMemberAPIView.as_view(), name="current-member"),
]