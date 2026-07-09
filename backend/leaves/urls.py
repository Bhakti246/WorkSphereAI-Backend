from rest_framework.routers import DefaultRouter
from .views import LeaveViewSet

router = DefaultRouter()
router.register("leaves", LeaveViewSet)

urlpatterns = router.urls