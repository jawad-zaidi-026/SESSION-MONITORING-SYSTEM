from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),  # Homepage route
    path('send-email/', views.send_email, name='send_email'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('anomalies/', views.anomalies_view, name='anomalies'),
    path('dashboard/', views.dashboard_view, name='dashboard'),

]
