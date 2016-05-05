"""StateBike URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.8/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Add an import:  from blog import urls as blog_urls
    2. Add a URL to urlpatterns:  url(r'^blog/', include(blog_urls))
"""
from django.conf.urls import include, url
from django.contrib import admin
from Sbike import views

urlpatterns = [

    url(r'^$', views.home),
    url(r'^admin/', include(admin.site.urls)),
    url(r'^home/$', views.home, name='home'),
    url(r'^weblogin/$', views.webLoginView, name='web_login'),
    url(r'^logout/$', views.logoutView, name='logout'),
    url(r'^stationlogin/$', views.stationLoginView, name='station_login'),
    url(r'^register/$', views.clientRegisterView, name='client_register'),
    url(r'^stations/$', views.locatorView),
    url(r'^stationprofile/$', views.stationProfile),
    url(r'^editpassword/$', views.clientEditPassword),
    url(r'^editprofile/card$', views.clientEditCardData),
    url(r'^editprofile/phone$', views.ClientEditPhone),
    url(r'^editprofile/email$', views.ClientEditEmail),
    url(r'^webprofile/$', views.webProfile),
    url(r'^setstatus/$', views.setBikeStatus),
    url(r'^bikeloan/$', views.bikeLoan),
    url(r'^giveback/$', views.givebackView),
    url(r'^assignemployee/$', views.assignEmployee),
    url(r'^unassignemployee/$', views.unassignEmployee),
    url(r'^assignstation/$', views.assignStation),
    url(r'^unassignstation/$', views.unassignStation),
    url(r'^createstation/$', views.createStation),
    url(r'^viewclients/$', views.viewClients),
    url(r'^viewclients/(?P<username>.+)/$', views.viewClients),
    url(r'^movebike/$', views.moveBike),
    url(r'^addbikes/$', views.addBike),
    url(r'^employeeregister/$', views.employeeRegister),
    url(r'^about/$', views.about),
    url(r'^contact/$', views.contact),
    url(r'^employeeconsult/$', views.employeeConsult)
]
