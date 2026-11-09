from django.db import models
from django.contrib.auth.models import User  # Django built-in User model for Register / Login / JWT


# ==============================================================================
# 1. MASTER STUDENT MODEL (Primary Entity)
# ==============================================================================
class MasterStudent(models.Model):
    class CourseStatus(models.TextChoices):
        # Standard statuses
        ONGOING = "Ongoing", "Ongoing"
        COMPLETED = "Completed", "Completed"
        PROJECT = "Project", "Project"
        DROP = "Drop", "Drop"

        # Batch Switch initial option (for dropdown / button trigger)
        BATCHSWITCH = "Batchswitch", "Batchswitch"

        # Post-Rejoin statuses
        BATCHSWITCH_ONGOING = "Batchswitch/Ongoing", "Batchswitch/Ongoing"
        BATCHSWITCH_DROP = "Batchswitch/Drop", "Batchswitch/Drop"
        BATCHSWITCH_PROJECT = "Batchswitch/Project", "Batchswitch/Project"
        BATCHSWITCH_COMPLETED = "Batchswitch/Completed", "Batchswitch/Completed"

    class FeeStatus(models.TextChoices):
        COMPLETED = "completed", "Completed"
        NOT_COMPLETED = "Notcompleted", "Not Completed"

    class ProjectStatus(models.TextChoices):
        COMPLETED = "completed", "Completed"
        NOT_COMPLETED = "Notcompleted", "Not Completed"

    class PlacementStatus(models.TextChoices):
        YES = "Yes", "Yes"
        NO = "No", "No (not eligible)"

    # Primary Key
    id = models.BigAutoField(primary_key=True)

    # 1. Sl. No (Unique serial number)
    si_no = models.PositiveIntegerField(unique=True, verbose_name="Sl. No")

    # 2 - 8. Basic Student Details
    name = models.CharField(max_length=150)
    course = models.CharField(max_length=100)
    batch_name = models.CharField(max_length=100)
    month = models.CharField(max_length=20)
    year = models.PositiveIntegerField()
    phone = models.CharField(max_length=20)
    email_id = models.EmailField(unique=True)

    # 9 - 11. Status Fields
    course_status = models.CharField(
        max_length=30,
        choices=CourseStatus.choices,
        default=CourseStatus.ONGOING,
    )
    fee_status = models.CharField(
        max_length=20,
        choices=FeeStatus.choices,
        default=FeeStatus.NOT_COMPLETED,
    )
    project_status = models.CharField(
        max_length=20,
        choices=ProjectStatus.choices,
        default=ProjectStatus.NOT_COMPLETED,
    )

    # 12. Auto Eligibility (Eligible when Fee=completed AND Project=completed)
    is_eligible = models.BooleanField(
        default=False,
        editable=False,
        verbose_name="Eligible Status",
    )

    # 13. Placement Status
    placement_status = models.CharField(
        max_length=10,
        choices=PlacementStatus.choices,
        default=PlacementStatus.NO,
    )

    # 14. Remarks
    remarks = models.TextField(blank=True, null=True)

    class Meta:
        db_table = "master_students"
        ordering = ["si_no"]

    def save(self, *args, **kwargs):
        # 12. Automatic calculation of eligibility
        if (
            self.fee_status == self.FeeStatus.COMPLETED
            and self.project_status == self.ProjectStatus.COMPLETED
        ):
            self.is_eligible = True
        else:
            self.is_eligible = False
            # 13. If not eligible, placement status automatically defaults to 'No'
            self.placement_status = self.PlacementStatus.NO

        super().save(*args, **kwargs)

    def rejoin_batch(self, new_course, new_batch):
        """
        Helper method called when submitting the Rejoin pop-up form.
        Creates a BatchSwitch record and updates this student's details.
        """
        return BatchSwitch.objects.create(
            student=self,
            new_course=new_course,
            new_batch=new_batch,
        )

    def __str__(self):
        return f"{self.si_no} - {self.name} ({self.batch_name})"


# ==============================================================================
# 2. BATCH TABLE (Foreign Key link to Master Student)
# ==============================================================================
class Batch(models.Model):
    """
    Batch Table connected via Foreign Key to MasterStudent.
    All student details are dynamically fetched from MasterStudent.
    """
    id = models.BigAutoField(primary_key=True)

    # FOREIGN KEY to MasterStudent
    student = models.ForeignKey(
        MasterStudent,
        on_delete=models.CASCADE,
        related_name="batch_entries",
    )
    batch_name = models.CharField(max_length=100, db_index=True)

    # Dynamic properties fetched from Master Student via Foreign Key
    @property
    def name(self):
        return self.student.name

    @property
    def email(self):
        return self.student.email_id

    @property
    def phone(self):
        return self.student.phone

    @property
    def course_status(self):
        return self.student.course_status

    @property
    def fee_status(self):
        return self.student.fee_status

    @property
    def project_status(self):
        return self.student.project_status

    @property
    def is_eligible(self):
        return self.student.is_eligible

    @property
    def placement_status(self):
        return self.student.placement_status

    class Meta:
        db_table = "batch_records"

    def __str__(self):
        return f"{self.batch_name} - {self.student.name}"


# ==============================================================================
# 3. BATCH SWITCH TABLE (Foreign Key link to Master Student + Switch History)
# ==============================================================================
class BatchSwitch(models.Model):
    """
    Maintains an audit history of batch switches.
    Automatically updates MasterStudent when a switch record is created:
    - Sets new batch name and new course
    - Sets course_status to 'Batchswitch/Ongoing'
    """
    id = models.BigAutoField(primary_key=True)

    # FOREIGN KEY to MasterStudent
    student = models.ForeignKey(
        MasterStudent,
        on_delete=models.CASCADE,
        related_name="batch_switches",
    )

    # Historical values captured automatically from student before switch
    old_course = models.CharField(max_length=100, blank=True)
    old_batch = models.CharField(max_length=100, blank=True)

    # New inputs entered from the Rejoin form
    new_course = models.CharField(max_length=100)
    new_batch = models.CharField(max_length=100)

    # Switch timestamp
    switched_at = models.DateTimeField(auto_now_add=True)

    # Dynamic properties fetched from Master Student via Foreign Key
    @property
    def name(self):
        return self.student.name

    @property
    def email(self):
        return self.student.email_id

    @property
    def phone(self):
        return self.student.phone

    class Meta:
        db_table = "batch_switches"
        ordering = ["-switched_at"]

    def save(self, *args, **kwargs):
        # Runs on new switch creation (Rejoin submit)
        if not self.pk:
            # 1. Capture current course & batch from Master Student as 'old'
            if not self.old_course:
                self.old_course = self.student.course
            if not self.old_batch:
                self.old_batch = self.student.batch_name

            # 2. Update Master Student with new values and switch status
            self.student.course = self.new_course
            self.student.batch_name = self.new_batch
            self.student.course_status = MasterStudent.CourseStatus.BATCHSWITCH_ONGOING
            self.student.save()

            # 3. Add an entry in the Batch Table for the new batch
            Batch.objects.create(
                student=self.student,
                batch_name=self.new_batch,
            )

        super().save(*args, **kwargs)

    def __str__(self):
        return f"Switch: {self.student.name} ({self.old_batch} -> {self.new_batch})"