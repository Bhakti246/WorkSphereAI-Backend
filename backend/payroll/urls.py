from rest_framework.routers import DefaultRouter
from .views import PayrollViewSet

router = DefaultRouter()
router.register(
    "payroll",
    PayrollViewSet
)

urlpatterns = router.urls