from django.urls import path
from . import views

app_name = "references"

urlpatterns = [
    path("api/departments/", views.departments_by_institute, name="departments_api"),
    path("api/specialties/", views.specialties_by_institute_and_level, name="specialties_api"),
]