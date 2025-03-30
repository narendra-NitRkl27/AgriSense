#This will contain basic url part
from django.urls import path
from  . import views

urlpatterns=[
    path('', views.weather_view, name='weather View')
]#it will work in the base url model where when user will visit base url then they will recive the response from the weather view function created 