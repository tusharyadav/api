from django.conf.urls import include, url
from django.contrib import admin
from api.api_views import *

##
#	Service routes
#
##
urlpatterns = [
    url(r'^admin/', include(admin.site.urls)),
    url(r'^common-word/', CommonWords.as_view(), name="CommonWords"),
]
