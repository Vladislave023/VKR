from django.urls import path
from . import views

app_name = "submissions"

urlpatterns = [
    path("", views.my_submissions_view, name="my_list"),
    path("new/", views.submission_create_view, name="create"),
    path("<int:pk>/", views.submission_detail_view, name="detail"),
    path("<int:pk>/edit/", views.submission_edit_view, name="edit"),
]
