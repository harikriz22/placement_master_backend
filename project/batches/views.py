from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.db.models import Count
from students.models import Batch,Student
from .serializers import BatchSerializer
from django.db.models import Q
from students.serializers import StudentSerializer



class BatchListCreateAPIView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        batches = Batch.objects.all()
        serializer = BatchSerializer(batches, many=True)

        return Response({
            "success": True,
            "message": "Batches retrieved successfully.",
            "data": serializer.data
        }, status=status.HTTP_200_OK)

    # Create a new batch
    def post(self, request):

        serializer = BatchSerializer(data=request.data)

        if serializer.is_valid():
            serializer.save()

            return Response({
                "success": True,
                "message": "Batch created successfully.",
                "data": serializer.data
            }, status=status.HTTP_201_CREATED)

        return Response({
            "success": False,
            "message": "Batch creation failed.",
            "errors": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)
        

class BatchDetailAPIView(APIView):

    permission_classes = [IsAuthenticated]

    def get_object(self, pk):
        try:
            return Batch.objects.get(pk=pk)
        except Batch.DoesNotExist:
            return None

    # Retrieve a single batch
    def get(self, request, pk):

        batch = self.get_object(pk)

        if batch is None:
            return Response({
                "success": False,
                "message": "Batch not found."
            }, status=status.HTTP_404_NOT_FOUND)

        serializer = BatchSerializer(batch)

        return Response({
            "success": True,
            "message": "Batch retrieved successfully.",
            "data": serializer.data
        }, status=status.HTTP_200_OK)

    # Update a batch
    def put(self, request, pk):

        batch = self.get_object(pk)

        if batch is None:
            return Response({
                "success": False,
                "message": "Batch not found."
            }, status=status.HTTP_404_NOT_FOUND)

        serializer = BatchSerializer(batch, data=request.data)

        if serializer.is_valid():
            serializer.save()

            return Response({
                "success": True,
                "message": "Batch updated successfully.",
                "data": serializer.data
            }, status=status.HTTP_200_OK)

        return Response({
            "success": False,
            "message": "Batch update failed.",
            "errors": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

    # Partially update a batch
    def patch(self, request, pk):

        batch = self.get_object(pk)

        if batch is None:
            return Response({
                "success": False,
                "message": "Batch not found."
            }, status=status.HTTP_404_NOT_FOUND)

        serializer = BatchSerializer(
            batch,
            data=request.data,
            partial=True
        )

        if serializer.is_valid():
            serializer.save()

            return Response({
                "success": True,
                "message": "Batch updated successfully.",
                "data": serializer.data
            }, status=status.HTTP_200_OK)

        return Response({
            "success": False,
            "message": "Batch update failed.",
            "errors": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)
        
        
        
class CourseListAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        courses = (
            Batch.objects
            .values("course")
            .annotate(
                total_batches=Count("id", distinct=True),
                total_students=Count("students", distinct=True)
            )
            .order_by("course")
        )

        return Response({
            "success": True,
            "message": "Courses retrieved successfully.",
            "data": courses
        }, status=status.HTTP_200_OK)
        

class BatchStudentsAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        try:
            batch = Batch.objects.get(pk=pk)
        except Batch.DoesNotExist:
            return Response(
                {
                    "success": False,
                    "message": "Batch not found."
                },
                status=status.HTTP_404_NOT_FOUND
            )

        students = Student.objects.filter(batch=batch).select_related(
            "batch",
            "updated_by"
        )

        counts = students.aggregate(
            total_students=Count("id"),

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
            )
        )

        counts["not_eligible"] = (
            counts["total_students"] - counts["eligible"]
        )

        serializer = StudentSerializer(students, many=True)

        return Response(
            {
                "success": True,
                "message": "Batch details retrieved successfully.",
                "data": {
                    "batch": BatchSerializer(batch).data,
                    "counts": counts,
                    "students": serializer.data
                }
            },
            status=status.HTTP_200_OK
        )
        
