from rest_framework import serializers
from students.models import Student, Batch


class StudentImportRowSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=150)
    email = serializers.EmailField(required=False,allow_null=True,allow_blank=True)
    phone = serializers.CharField(max_length=20)
    batch = serializers.CharField()

    course_status = serializers.ChoiceField(
        choices=Student.CourseStatus.choices
    )

    fee_completed = serializers.BooleanField(
        required=False,
        allow_null=True
    )

    project_completed = serializers.BooleanField(
        required=False,
        allow_null=True
    )

    placement_status = serializers.ChoiceField(
        choices=Student.PlacementStatus.choices,
        required=False,
        allow_blank=True
    )

    remarks = serializers.CharField(required=False, allow_blank=True)
    qualification = serializers.CharField(required=False, allow_blank=True)
    passout_year = serializers.IntegerField(required=False, allow_null=True)
    college_name = serializers.CharField(required=False, allow_blank=True)
    module_evaluation = serializers.CharField(required=False, allow_blank=True)
    mock_presentation = serializers.CharField(required=False, allow_blank=True)
    trainer_feedback = serializers.CharField(required=False, allow_blank=True)
    hr_feedback = serializers.CharField(required=False, allow_blank=True)

    resume_session = serializers.BooleanField(required=False, allow_null=True)
    interview_session = serializers.BooleanField(required=False, allow_null=True)

    def validate_batch(self, value):
        try:
            course, month, year, batch_number = [
                item.strip() for item in value.split("|")
            ]

            Batch.objects.get(
                course=course,
                month=month,
                year=int(year),
                batch_number=int(batch_number)
            )

        except (ValueError, Batch.DoesNotExist):
            raise serializers.ValidationError(
                "Invalid batch reference or batch does not exist."
            )

        return value