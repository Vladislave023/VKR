from django.urls import path
from . import views

app_name = "references"

urlpatterns = [
    path("references/", views.ReferenceDashboardView.as_view(), name="dashboard"),
    path("references/upload/kug/", views.UploadKugView.as_view(), name="upload_kug"),
    path("references/upload/sr/", views.UploadSrView.as_view(), name="upload_sr"),
    path("references/imports/", views.ImportListView.as_view(), name="import_list"),
    path("references/imports/<int:pk>/", views.ImportDetailView.as_view(), name="import_detail"),
    path("api/departments/", views.departments_by_institute, name="departments_api"),
    path("api/specialties/", views.specialties_by_institute_and_level, name="specialties_api"),
]
