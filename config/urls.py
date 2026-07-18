from django.contrib import admin
from django.urls import path, include
from django.http import JsonResponse
from django.conf import settings
from django.conf.urls.static import static


def home(request):
    return JsonResponse({
        "status": "Backend is running successfully 🚀"
    })


urlpatterns = [
    path("", home, name="home"),
    path("admin/", admin.site.urls),

    path("api/auth/", include("accounts.urls")),
    path("api/candidates/", include("candidates.urls")),
    path("api/jobs/", include("jobs.urls")),
    path("api/interviews/", include("interviews.urls")),
    path("api/ai/", include("ai_features.urls")),
    path("api/assessments/", include("assessments.urls")),
]

# Serve media files
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)