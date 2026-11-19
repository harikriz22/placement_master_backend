from collections import defaultdict

from openpyxl import load_workbook

from django.db import transaction
from django.db.models import Q

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework import status

from students.models import Student, Batch
from .serializers import StudentImportRowSerializer


def get_batch_from_reference(reference):
    """
    Resolve Excel batch reference to a Batch object.

    Expected format:
    Course | Month | Year | Batch Number
    """

    course, month, year, batch_number = [
        value.strip()
        for value in reference.split("|")
    ]

    return Batch.objects.get(
        course=course,
        month=month,
        year=int(year),
        batch_number=int(batch_number)
    )


def get_student_identity_key(name, phone, batch_id):
    """
    Generate a normalized identity key for students
    whose email address is missing.
    """

    return (
        str(name).strip().casefold(),
        str(phone).strip(),
        batch_id
    )


class StudentImportPreviewView(APIView):

    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request):

        excel_file = request.FILES.get("file")

        if not excel_file:
            return Response(
                {"error": "Please upload an Excel file."},
                status=status.HTTP_400_BAD_REQUEST
            )

        if not excel_file.name.lower().endswith(".xlsx"):
            return Response(
                {"error": "Only .xlsx files are supported."},
                status=status.HTTP_400_BAD_REQUEST
            )

        workbook = None

        try:

            workbook = load_workbook(
                excel_file,
                read_only=True,
                data_only=True
            )

            if "Students_Import" not in workbook.sheetnames:

                return Response(
                    {"error": "Students_Import sheet not found."},
                    status=status.HTTP_400_BAD_REQUEST
                )

            sheet = workbook["Students_Import"]

            headers = [
                cell.value
                for cell in next(
                    sheet.iter_rows(min_row=1, max_row=1)
                )
            ]

            required_columns = [
                "name",
                "email",
                "phone",
                "batch",
                "course_status",
                "fee_completed",
                "project_completed",
                "placement_status",
            ]

            missing_columns = [
                column
                for column in required_columns
                if column not in headers
            ]

            if missing_columns:

                return Response(
                    {
                        "error": "Required columns are missing.",
                        "missing_columns": missing_columns
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )

            boolean_fields = [
                "fee_completed",
                "project_completed",
                "resume_session",
                "interview_session",
            ]

            optional_text_fields = [
                "remarks",
                "qualification",
                "college_name",
                "module_evaluation",
                "mock_presentation",
                "trainer_feedback",
                "hr_feedback",
            ]

            processed_rows = []

            email_occurrences = defaultdict(list)

            identity_occurrences = defaultdict(list)

            batch_cache = {}

            # --------------------------------------------------
            # 1. READ AND VALIDATE EXCEL ROWS
            # --------------------------------------------------

            for row_number, row in enumerate(
                sheet.iter_rows(min_row=2, values_only=True),
                start=2
            ):

                if not any(value is not None for value in row):
                    continue

                row_data = dict(zip(headers, row))

                # Normalize name and phone
                if row_data.get("name") is not None:
                    row_data["name"] = str(
                        row_data["name"]
                    ).strip()

                if row_data.get("phone") is not None:
                    row_data["phone"] = str(
                        row_data["phone"]
                    ).strip()

                # Normalize optional text fields
                for field in optional_text_fields:

                    if row_data.get(field) is None:
                        row_data[field] = ""

                # Default course status
                if not row_data.get("course_status"):

                    row_data["course_status"] = (
                        Student.CourseStatus.ONGOING
                    )

                # Default placement status
                if not row_data.get("placement_status"):

                    row_data["placement_status"] = (
                        Student.PlacementStatus.PROJECT_NOT_COMPLETED
                    )

                # Normalize boolean fields
                for field in boolean_fields:

                    value = row_data.get(field)

                    if isinstance(value, bool):
                        continue

                    if value is None or str(value).strip() == "":
                        row_data[field] = None

                    elif str(value).strip().lower() in [
                        "true", "yes", "1"
                    ]:
                        row_data[field] = True

                    elif str(value).strip().lower() in [
                        "false", "no", "0"
                    ]:
                        row_data[field] = False

                # Normalize email
                email = row_data.get("email")

                if email is not None:
                    email = str(email).strip().lower()

                if not email:
                    email = None
                    row_data["email"] = None

                else:
                    row_data["email"] = email
                    email_occurrences[email].append(row_number)

                # Validate row
                serializer = StudentImportRowSerializer(
                    data=row_data
                )

                if serializer.is_valid():

                    errors = {}
                    validated_data = serializer.validated_data

                else:

                    errors = dict(serializer.errors)
                    validated_data = None

                processed_rows.append({
                    "row": row_number,
                    "name": row_data.get("name"),
                    "email": email,
                    "data": validated_data,
                    "errors": errors,
                })

            # --------------------------------------------------
            # 2. FIND DUPLICATE EMAILS INSIDE EXCEL
            # --------------------------------------------------

            duplicate_emails = {
                email: rows
                for email, rows in email_occurrences.items()
                if len(rows) > 1
            }

            # --------------------------------------------------
            # 3. FIND EMAILS ALREADY IN DATABASE
            # --------------------------------------------------

            existing_emails = set()

            if email_occurrences:

                email_query = Q()

                for email in email_occurrences:
                    email_query |= Q(email__iexact=email)

                existing_emails = {
                    email.lower()
                    for email in Student.objects.filter(
                        email_query
                    ).values_list("email", flat=True)
                    if email
                }

            # --------------------------------------------------
            # 4. FIND EMAIL-LESS DUPLICATES INSIDE EXCEL
            # --------------------------------------------------

            for item in processed_rows:

                if item["errors"] or item["email"]:
                    continue

                student_data = item["data"]

                batch_reference = student_data["batch"]

                if batch_reference not in batch_cache:

                    batch_cache[batch_reference] = (
                        get_batch_from_reference(batch_reference)
                    )

                batch = batch_cache[batch_reference]

                identity_key = get_student_identity_key(
                    student_data["name"],
                    student_data["phone"],
                    batch.id
                )

                identity_occurrences[identity_key].append(
                    item["row"]
                )

            duplicate_identities = {
                key: rows
                for key, rows in identity_occurrences.items()
                if len(rows) > 1
            }

            # --------------------------------------------------
            # 5. FIND EMAIL-LESS DUPLICATES IN DATABASE
            # --------------------------------------------------

            existing_identity_keys = set()

            identity_query = Q()

            for identity_key in identity_occurrences:

                name, phone, batch_id = identity_key

                identity_query |= Q(
                    name__iexact=name,
                    phone=phone,
                    batch_id=batch_id
                )

            if identity_occurrences:

                existing_students = Student.objects.filter(
                    identity_query
                ).values(
                    "name",
                    "phone",
                    "batch_id"
                )

                existing_identity_keys = {
                    get_student_identity_key(
                        student["name"],
                        student["phone"],
                        student["batch_id"]
                    )
                    for student in existing_students
                }

            # --------------------------------------------------
            # 6. BUILD FINAL PREVIEW RESPONSE
            # --------------------------------------------------

            valid_students = []
            invalid_students = []

            for item in processed_rows:

                email = item["email"]
                row_number = item["row"]

                errors = item["errors"]

                if email and email in duplicate_emails:

                    errors["email"] = [
                        "Duplicate email found in uploaded Excel file."
                    ]

                elif email and email in existing_emails:

                    errors["email"] = [
                        "This email already exists in the database."
                    ]

                elif not email and item["data"]:

                    student_data = item["data"]

                    batch_reference = student_data["batch"]
                    batch = batch_cache[batch_reference]

                    identity_key = get_student_identity_key(
                        student_data["name"],
                        student_data["phone"],
                        batch.id
                    )

                    if identity_key in duplicate_identities:

                        errors["duplicate"] = [
                            "Duplicate student found in uploaded Excel file with the same name, phone number and batch."
                        ]

                    elif identity_key in existing_identity_keys:

                        errors["duplicate"] = [
                            "Student already exists in the database with the same name, phone number and batch."
                        ]

                if errors:

                    invalid_students.append({
                        "row": row_number,
                        "name": item["name"],
                        "errors": errors,
                    })

                else:

                    valid_students.append({
                        "row": row_number,
                        "data": item["data"],
                    })

            return Response({
                "message": "Excel preview completed.",
                "total_students": len(processed_rows),
                "valid_count": len(valid_students),
                "invalid_count": len(invalid_students),
                "valid_students": valid_students,
                "invalid_students": invalid_students,
            })

        except Exception as error:

            return Response(
                {
                    "error": f"Unable to process Excel file: {str(error)}"
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        finally:

            if workbook:
                workbook.close()


class StudentImportConfirmView(APIView):

    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request):

        # Revalidate the uploaded Excel file
        preview_view = StudentImportPreviewView()

        preview_response = preview_view.post(request)

        if preview_response.status_code != status.HTTP_200_OK:
            return preview_response

        preview_data = preview_response.data

        valid_students = preview_data["valid_students"]

        skipped_students = list(
            preview_data["invalid_students"]
        )

        imported_count = 0

        try:

            with transaction.atomic():

                for item in valid_students:

                    student_data = item["data"].copy()

                    # Resolve batch
                    batch_reference = student_data.pop("batch")

                    batch = get_batch_from_reference(
                        batch_reference
                    )

                    email = student_data.get("email")

                    # ------------------------------------------
                    # RECHECK DUPLICATES BEFORE SAVING
                    # ------------------------------------------

                    if email:

                        duplicate_exists = Student.objects.filter(
                            email__iexact=email
                        ).exists()

                        if duplicate_exists:

                            skipped_students.append({
                                "row": item["row"],
                                "name": student_data["name"],
                                "errors": {
                                    "email": [
                                        "This email already exists in the database."
                                    ]
                                }
                            })

                            continue

                    else:

                        duplicate_exists = Student.objects.filter(
                            name__iexact=student_data["name"].strip(),
                            phone=student_data["phone"].strip(),
                            batch=batch
                        ).exists()

                        if duplicate_exists:

                            skipped_students.append({
                                "row": item["row"],
                                "name": student_data["name"],
                                "errors": {
                                    "duplicate": [
                                        "Student already exists with the same name, phone number and batch."
                                    ]
                                }
                            })

                            continue

                    # ------------------------------------------
                    # APPLY DEFAULT BOOLEAN VALUES
                    # ------------------------------------------

                    if student_data.get("fee_completed") is None:
                        student_data["fee_completed"] = False

                    if student_data.get("project_completed") is None:
                        student_data["project_completed"] = False

                    # ------------------------------------------
                    # ASSIGN BATCH AND USER
                    # ------------------------------------------

                    student_data["batch"] = batch

                    student_data["updated_by"] = request.user

                    # ------------------------------------------
                    # CREATE STUDENT
                    # ------------------------------------------

                    Student.objects.create(**student_data)

                    imported_count += 1

            return Response(
                {
                    "message": "Student import completed successfully.",
                    "total_students": preview_data["total_students"],
                    "imported_count": imported_count,
                    "skipped_count": len(skipped_students),
                    "skipped_students": skipped_students,
                },
                status=(
                    status.HTTP_201_CREATED
                    if imported_count > 0
                    else status.HTTP_200_OK
                )
            )

        except Exception as error:

            return Response(
                {
                    "error": f"Student import failed: {str(error)}",
                    "imported_count": 0,
                },
                status=status.HTTP_400_BAD_REQUEST
            )