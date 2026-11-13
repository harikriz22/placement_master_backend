from django.shortcuts import render
from rest_framework.response import IsAuthenticated



from .models import MasterStudent
from .serializers import MasterStudentSerializer

# Create your views here.
class StudentListCreateAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):

        students = MasterStudent.objects.all()
