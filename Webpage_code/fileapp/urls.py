from django.urls import path
from .views import delete_file, delete_success, index, upload_file, download_file
from fileapp import views

urlpatterns = [
    path("", index, name="index"),
    path("upload/", upload_file, name="upload"),
    path('download/<int:id>/', download_file, name='download'),
    path("delete/<path:file_key>/", delete_file, name="delete_file"),
    path('delete/success/', delete_success, name='delete_success'),
]
