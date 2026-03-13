from django.urls import path
from care_engine import views

urlpatterns = [
    path('conditions/', views.conditions_list, name='conditions-list'),
    path('providers/', views.providers_list, name='providers-list'),
    path('medications/', views.medications_list, name='medications-list'),
    path('score/', views.score, name='score'),
    path('reasoning/', views.reasoning, name='reasoning'),
    path('plans/', views.plans_list, name='plans-list'),
]
