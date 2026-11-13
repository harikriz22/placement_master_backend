from django.db import models
from django.conf import settings


class Batch(models.Model):
    class Month(models.TextChoices):
        JANUARY = "January", "January"
        FEBRUARY = "February", "February"
        MARCH = "March", "March"
        APRIL = "April", "April"
        MAY = "May", "May"
        JUNE = "June", "June"
        JULY = "July", "July"
        AUGUST = "August", "August"
        SEPTEMBER = "September", "September"
        OCTOBER = "October", "October"
        NOVEMBER = "November", "November"
        DECEMBER = "December", "December"

    id = models.BigAutoField(primary_key=True)
    course = models.CharField(max_length=100)
    month = models.CharField(max_length=20,choices=Month.choices)
    year = models.PositiveIntegerField()
    batch_number = models.PositiveSmallIntegerField(default=1)

    class Meta:
        ordering = ["-year", "month", "course"]
        constraints = [
            models.UniqueConstraint(
                fields=["course", "month", "year", "batch_number"],
                name="unique_course_batch"
            )
        ]


    def __str__(self):
        return f"{self.course} {self.month} {self.year} - {self.batch_number}"


class Student(models.Model):

    class CourseStatus(models.TextChoices):
        ONGOING = "Ongoing", "Ongoing"
        COMPLETED = "Completed", "Completed"
        PROJECT = "Project", "Project"
        DROP = "Drop", "Drop"
        HOLD = "Hold", "Hold"
        REJOINED = "Rejoined", "Rejoined"

        BATCHSWITCH_ONGOING = "BatchSwitch/ongoing", "BatchSwitch/ongoing"
        BATCHSWITCH_COMPLETED = "BatchSwitch/completed", "BatchSwitch/completed"
        BATCHSWITCH_REJOINED = "BatchSwitch/rejoined", "BatchSwitch/rejoined"
        BATCHSWITCH_DROPPED = "BatchSwitch/dropped", "BatchSwitch/dropped"

    class PlacementStatus(models.TextChoices):
        PLACEMENT_NEEDED = "Placement needed", "Placement needed"
        PLACED = "Placed", "Placed"
        PROJECT_NOT_COMPLETED = "Project not completed", "Project not completed"
        PLACEMENT_NOT_NEEDED = "Placement not needed", "Placement not needed"

    id = models.BigAutoField(primary_key=True)
    name = models.CharField(max_length=150)
    email = models.EmailField()
    phone = models.CharField(max_length=20)
    batch = models.ForeignKey(Batch,on_delete=models.PROTECT,related_name="students")

    course_status = models.CharField(max_length=30,choices=CourseStatus.choices,default=CourseStatus.ONGOING)
    fee_completed = models.BooleanField(default=False)
    project_completed = models.BooleanField(default=False)

    placement_status = models.CharField(
        max_length=30,
        choices=PlacementStatus.choices,
        default=PlacementStatus.PROJECT_NOT_COMPLETED
    )

    remarks = models.TextField(blank=True)

    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="updated_students"
    )

    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name
    


class BatchSwitchHistory(models.Model):

    student = models.ForeignKey(
        Student,
        on_delete=models.PROTECT,
        related_name="batch_switch_history"
    )

    previous_batch = models.ForeignKey(
        Batch,
        on_delete=models.PROTECT,
        related_name="previous_batch_switches"
    )

    new_batch = models.ForeignKey(
        Batch,
        on_delete=models.PROTECT,
        related_name="new_batch_switches"
    )

    reason = models.TextField(blank=True)

    switched_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="batch_switches"
    )

    switched_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-switched_at"]

    def __str__(self):
        return f"{self.student.name}: {self.previous_batch} -> {self.new_batch}"