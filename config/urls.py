from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.views.static import serve as _static_serve


def _serve_attachment(request, path, document_root=None):
    # Force download + disable MIME sniffing so uploaded files never execute inline.
    response = _static_serve(request, path, document_root=document_root)
    response['Content-Disposition'] = 'attachment'
    response['X-Content-Type-Options'] = 'nosniff'
    return response


urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('submissions.urls')),
    path('media/<path:path>', _serve_attachment, {'document_root': settings.MEDIA_ROOT}),
]
