from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    AutomationScriptViewSet, ScriptExecutionViewSet, ScriptTemplateViewSet
)

router = DefaultRouter()
router.register(r'scripts', AutomationScriptViewSet, basename='automation-script')
router.register(r'executions', ScriptExecutionViewSet, basename='script-execution')
router.register(r'templates', ScriptTemplateViewSet, basename='script-template')

urlpatterns = [
    path('api/automation-scripts/', include(router.urls)),
]