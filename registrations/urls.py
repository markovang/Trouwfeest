from django.urls import path
from . import views

urlpatterns = [
    path('', views.register, name='register'),
    path('aanmelden/<slug:step>/', views.registration_step, name='registration_step'),
    path('bedankt/', views.confirmation, name='confirmation'),
]
