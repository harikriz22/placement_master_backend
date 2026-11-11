from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, serializers
from rest_framework.permissions import IsAuthenticated
from rest_framework.pagination import PageNumberPagination
from django.db.models import Q
from .models import Student, Batch,BatchSwitchHistory
from .serializers import StudentSerializer,BatchSwitchSerializer,BatchSwitchHistorySerializer
from django.db import transaction


# Pagination
class StudentPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = "page_size"
    max_page_size = 100


class StudentListCreateAPIView(APIView):
    permission_classes = [IsAuthenticated]

    # Boolean validation
    def get_boolean_param(self, request, parameter):
        value = request.query_params.get(parameter)

        if value is None:
            return None

        value = value.lower()

        if value in ["true", "1", "yes"]:
            return True

        if value in ["false", "0", "no"]:
            return False

        raise serializers.ValidationError({
            parameter: "Enter a valid boolean value (true or false)."
        })


    # Choice validation
    def validate_choice_param(self, request, parameter, choices):
        value = request.query_params.get(parameter)

        if value is None:
            return None

        valid_choices = [choice[0] for choice in choices]

        if value not in valid_choices:
            raise serializers.ValidationError({
                parameter: f"Invalid value. Allowed values are: {valid_choices}"
            })

        return value

    # Batch validation
    def get_batch_param(self, request):
        batch = request.query_params.get("batch")

        if batch is None:
            return None

        if not batch.isdigit() or int(batch) <= 0:
            raise serializers.ValidationError({
                "batch": "Enter a valid positive batch ID."
            })

        if not Batch.objects.filter(id=int(batch)).exists():
            raise serializers.ValidationError({
                "batch": "Batch with this ID does not exist."
            })

        return int(batch)

    # GET - List, search, filter and paginate students
    def get(self, request):

        students = Student.objects.select_related(
            "batch",
            "updated_by"
        )

        batch = self.get_batch_param(request)
        
        course_status = self.validate_choice_param(
            request,
            "course_status",
            Student.CourseStatus.choices
        )

        placement_status = self.validate_choice_param(
            request,
            "placement_status",
            Student.PlacementStatus.choices
        )

        fee_completed = self.get_boolean_param(
            request,
            "fee_completed"
        )

        project_completed = self.get_boolean_param(
            request,
            "project_completed"
        )

        eligible = self.get_boolean_param(
            request,
            "eligible"
        )

        # Search students
        search = request.query_params.get("search")

        if search:
            search_query = (
                Q(name__icontains=search)
                | Q(email__icontains=search)
                | Q(phone__icontains=search)
                | Q(batch__course__icontains=search)
                | Q(batch__month__icontains=search)
            )

            # Search by batch year
            if search.isdigit():
                search_query |= Q(batch__year=int(search))

            students = students.filter(search_query)

        # Filter by batch
        if batch is not None:
            students = students.filter(batch_id=batch)

        # Filter by course status
        if course_status is not None:
            students = students.filter(course_status=course_status)

        # Filter by fee status
        if fee_completed is not None:
            students = students.filter(fee_completed=fee_completed)

        # Filter by project status
        if project_completed is not None:
            students = students.filter(
                project_completed=project_completed
            )

        # Filter by placement status
        if placement_status is not None:
            students = students.filter(
                placement_status=placement_status
            )

        # Filter by eligibility
        if eligible is not None:

            eligible_condition = (
                Q(fee_completed=True)
                & Q(project_completed=True)
                & ~Q(course_status__in=[
                    Student.CourseStatus.DROP,
                    Student.CourseStatus.BATCHSWITCH_DROPPED
                ])
            )

            if eligible:
                students = students.filter(eligible_condition)

            else:
                students = students.filter(~eligible_condition)

        # Pagination
        paginator = StudentPagination()

        paginated_students = paginator.paginate_queryset(
            students,
            request,
            view=self
        )

        serializer = StudentSerializer(
            paginated_students,
            many=True
        )

        return Response(
            {
                "success": True,
                "message": "Students retrieved successfully.",
                "data": serializer.data,
                "pagination": {
                    "total_students": paginator.page.paginator.count,
                    "total_pages": paginator.page.paginator.num_pages,
                    "current_page": paginator.page.number,
                    "page_size": paginator.get_page_size(request),
                    "next": paginator.get_next_link(),
                    "previous": paginator.get_previous_link()
                }
            },
            status=status.HTTP_200_OK
        )

    
    def post(self, request):

        serializer = StudentSerializer(data=request.data)

        serializer.is_valid(raise_exception=True)

        student = serializer.save(updated_by=request.user)

        return Response(
            {
                "success": True,
                "message": "Student created successfully.",
                "data": StudentSerializer(student).data
            },
            status=status.HTTP_201_CREATED
        )


class StudentDetailAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get_object(self, pk):
        try:
            return Student.objects.select_related(
                "batch",
                "updated_by"
            ).get(pk=pk)

        except Student.DoesNotExist:
            return None

    def get(self, request, pk):

        student = self.get_object(pk)

        if student is None:
            return Response(
                {
                    "success": False,
                    "message": "Student not found.",
                    "data": None
                },
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = StudentSerializer(student)

        return Response(
            {
                "success": True,
                "message": "Student retrieved successfully.",
                "data": serializer.data
            },
            status=status.HTTP_200_OK
        )

    def put(self, request, pk):
        return self.update_student(request, pk, partial=False)

    def patch(self, request, pk):
        return self.update_student(request, pk, partial=True)

    def update_student(self, request, pk, partial):

        student = self.get_object(pk)

        if student is None:
            return Response(
                {
                    "success": False,
                    "message": "Student not found.",
                    "data": None
                },
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = StudentSerializer(
            student,
            data=request.data,
            partial=partial
        )

        serializer.is_valid(raise_exception=True)

        serializer.save(updated_by=request.user)

        return Response(
            {
                "success": True,
                "message": "Student updated successfully.",
                "data": serializer.data
            },
            status=status.HTTP_200_OK
        )

    def delete(self, request, pk):

        return Response(
            {
                "success": False,
                "message": "Student deletion is not allowed.",
                "data": None
            },
            status=status.HTTP_405_METHOD_NOT_ALLOWED
        )



class BatchSwitchAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):

        serializer = BatchSwitchSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(
                {
                    "success": False,
                    "message": "Invalid data.",
                    "errors": serializer.errors
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        new_batch = serializer.validated_data["new_batch"]
        reason = serializer.validated_data.get("reason", "")

        with transaction.atomic():

            student = Student.objects.select_for_update().select_related(
                "batch"
            ).filter(pk=pk).first()

            if not student:
                return Response(
                    {
                        "success": False,
                        "message": "Student not found."
                    },
                    status=status.HTTP_404_NOT_FOUND
                )

            if student.batch_id == new_batch.id:
                return Response(
                    {
                        "success": False,
                        "message": "Student is already in this batch."
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )

            previous_batch = student.batch

            BatchSwitchHistory.objects.create(
                student=student,
                previous_batch=previous_batch,
                new_batch=new_batch,
                reason=reason,
                switched_by=request.user
            )

            student.batch = new_batch
            student.updated_by = request.user
            student.save(update_fields=[
                "batch",
                "updated_by",
                "updated_at"
            ])

        return Response(
            {
                "success": True,
                "message": "Student batch switched successfully.",
                "data": {
                    "student_id": student.id,
                    "student_name": student.name,
                    "previous_batch": str(previous_batch),
                    "current_batch": str(new_batch)
                }
            },
            status=status.HTTP_200_OK
        )
        

class BatchSwitchHistoryAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):

        if not Student.objects.filter(pk=pk).exists():
            return Response(
                {
                    "success": False,
                    "message": "Student not found."
                },
                status=status.HTTP_404_NOT_FOUND
            )

        history = BatchSwitchHistory.objects.filter(
            student_id=pk
        ).select_related(
            "student",
            "previous_batch",
            "new_batch",
            "switched_by"
        )

        serializer = BatchSwitchHistorySerializer(
            history,
            many=True
        )

        return Response(
            {
                "success": True,
                "message": "Batch switch history retrieved successfully.",
                "data": serializer.data
            },
            status=status.HTTP_200_OK
        )

class AllBatchSwitchHistoryAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):

        history = BatchSwitchHistory.objects.select_related(
            "student",
            "previous_batch",
            "new_batch",
            "switched_by"
        ).all()

        serializer = BatchSwitchHistorySerializer(
            history,
            many=True
        )

        return Response(
            {
                "success": True,
                "message": "Batch switch history retrieved successfully.",
                "data": serializer.data
            },
            status=status.HTTP_200_OK
        )