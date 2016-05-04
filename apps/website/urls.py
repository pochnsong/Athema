from django.conf.urls import url
from .views import *


urlpatterns = [
    url(r'^$',  IndexView.as_view(), name="index"),
    url(r'^testing/(?P<pk>[-\w]+)', TestingView.as_view(), name="testing"),
]
