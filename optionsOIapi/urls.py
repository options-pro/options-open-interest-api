from django.contrib import admin
from django.urls import path
from optionsOIapi import views

urlpatterns = [
    path("admin/", admin.site.urls),
    path("getoi/<str:symbol>/<str:expiryDate>", views.getOptionOI),
    path("getexpirydate/", views.getExpiryDatesList),
    path("getfutureoi/<str:symbol>/<str:expiryDate>",views.getFutureOI),
]
