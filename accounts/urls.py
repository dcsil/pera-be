from django.urls import path
from .views import SignUpView, LoginView, LogoutView, LogoutAllView, DashboardView

urlpatterns = [
    path("sign-up/", SignUpView.as_view(), name="sign-up"),
    path("login/", LoginView.as_view(), name="login"),
    path("logout/", LogoutView.as_view(), name="logout"),
    path("logoutall/", LogoutAllView.as_view(), name="logoutall"),
    path("dashboard/", DashboardView.as_view(), name="dashboard"),
]
