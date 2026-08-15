from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'employees', views.EmployeeViewSet, basename='employee')
router.register(r'attendance', views.AttendanceViewSet, basename='attendance')
router.register(r'leaves', views.LeaveViewSet, basename='leave')
router.register(r'payroll', views.PayrollViewSet, basename='payroll')

urlpatterns = [
    path('attendance/check-in/', views.morning_scan, name='attendance-check-in'),
    path('attendance/check-out/', views.evening_scan, name='attendance-check-out'),
    path('attendance/stats/', views.attendance_stats, name='attendance-stats'),
    path('dashboard/stats/', views.dashboard_stats, name='dashboard-stats'),
    # Auth endpoints are exposed under `/api/auth/` from the project-level include
    path('reports/export-employees/', views.export_employees, name='export-employees'),
    path('reports/export-attendance/', views.export_attendance, name='export-attendance'),
    path('reports/export-leaves/', views.export_leaves, name='export-leaves'),
    path('reports/export-payroll/', views.export_payroll, name='export-payroll'),
    path('', include(router.urls)),
]
