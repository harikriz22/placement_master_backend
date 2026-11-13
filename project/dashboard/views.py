from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.db.models import Count, Q
from students.models import Student


class DashboardAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        dashboard_data = Student.objects.aggregate(

            enrolled=Count("id"),

            eligible=Count(
                "id",
                filter=(
                    Q(fee_completed=True)
                    & Q(project_completed=True)
                    & ~Q(course_status__in=[
                        Student.CourseStatus.DROP,
                        Student.CourseStatus.BATCHSWITCH_DROPPED
                    ])
                )
            ),

            dropped=Count(
                "id",
                filter=Q(course_status__in=[
                    Student.CourseStatus.DROP,
                    Student.CourseStatus.BATCHSWITCH_DROPPED
                ])
            ),

            batch_switch=Count(
                "id",
                filter=Q(course_status__startswith="BatchSwitch/")
            ),

            rejoined=Count(
                "id",
                filter=Q(course_status__in=[
                    Student.CourseStatus.REJOINED,
                    Student.CourseStatus.BATCHSWITCH_REJOINED
                ])
            ),
            
            placed=Count(
                "id",
                filter=Q(
                    placement_status=Student.PlacementStatus.PLACED
                )
            )
        )

        dashboard_data["not_eligible"] = (
            dashboard_data["enrolled"] - dashboard_data["eligible"]
        )

        return Response(
            {
                "success": True,
                "message": "Dashboard data retrieved successfully.",
                "data": dashboard_data
            },
            status=status.HTTP_200_OK
        )
