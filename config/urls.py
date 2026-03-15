
from django.contrib import admin

from django.conf import settings
from django.conf.urls.static import static

from django.urls import path, include

from catalog.views import HomeView

urlpatterns = [
    path("admin/", admin.site.urls),
    path('catalog/', include('catalog.urls')),
    path('cart/', include('cart.urls')),
    path('', HomeView.as_view(), name='home'),
]


if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)