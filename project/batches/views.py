from django.shortcuts import render

# Create your views here.
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated

from students.models import Batch
from .serializers import BatchSerializer


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