# blog/urls.py
from django.urls import path
from . import views  # On importe tes vues ici

urlpatterns = [
    path('', views.dashboard_view, name='root'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('suivi-demandes/', views.suivi_view, name='suivi_demandes'),
    path('suivi/detail/<str:id_flux>/<str:id_ise>/<str:id_da>/<str:id_ao>/<str:id_cmd>/', views.detail_flux, name='detail_flux'),
]