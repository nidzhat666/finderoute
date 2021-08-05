"""finderoute URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from django.conf import settings
from main import views
from django.contrib.staticfiles.urls import staticfiles_urlpatterns

urlpatterns = [
                  path('', views.main, name='main'),
                  path('get_route/', views.get_route, name='get_route'),
                  path('airport_data/', views.airport_data, name='airport_data'),
                  path('autocomplete/', views.autocomplete, name='autocomplete'),
                  path('autocomplete_icao/', views.autocomplete_icao, name='autocomplete_icao'),
                  path('metar_taf/', views.metar_taf, name="metar_taf"),
                  path('find_airport/', views.find_airport, name='find_airport'),
                  path('find_metar_taf/', views.find_metar_taf, name='find_metar_taf'),
                  path('nats/', views.nats, name='nats'),
                  path('admin/', admin.site.urls),
              ] + staticfiles_urlpatterns()
