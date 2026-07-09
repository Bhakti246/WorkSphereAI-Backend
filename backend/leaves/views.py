from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import Leave
from .serializers import LeaveSerializer


class LeaveViewSet(viewsets.ModelViewSet):
    queryset = Leave.objects.all()
    serializer_class = LeaveSerializer

    @action(detail=True, methods=["post"])
    def approve(self, request, pk=None):
        leave = self.get_object()
        leave.status = "Approved"
        leave.save()

        return Response({
            "message": "Leave approved"
        })

    @action(detail=True, methods=["post"])
    def reject(self, request, pk=None):
        leave = self.get_object()
        leave.status = "Rejected"
        leave.save()

        return Response({
            "message": "Leave rejected"
        })