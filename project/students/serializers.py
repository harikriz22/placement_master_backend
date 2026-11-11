from rest_framework import serializers
from .models import Student,Batch,BatchSwitchHistory

class StudentSerializer(serializers.ModelSerializer):
    
    batch_name=serializers.StringRelatedField(source="batch",read_only=True)
    eligible=serializers.SerializerMethodField()
    
    class Meta:
        model=Student
        fields=[
            "id","name","email","phone","batch","batch_name","course_status",
            "fee_completed","project_completed","eligible","placement_status",
            "remarks","updated_by","updated_at",
            ]
        
        read_only_fields = ["id","eligible","updated_by","updated_at",]
    
    
    def get_eligible(self, obj):
        return (
            obj.fee_completed
            and obj.project_completed
            and obj.course_status not in [
                Student.CourseStatus.DROP,
                Student.CourseStatus.BATCHSWITCH_DROPPED,
            ]
        )
        

    def validate(self, attrs):
        project_completed = attrs.get(
            "project_completed",
            getattr(self.instance, "project_completed", False)
        )
        placement_status = attrs.get(
            "placement_status",
            getattr(
                self.instance,
                "placement_status",
                Student.PlacementStatus.PROJECT_NOT_COMPLETED
            )
        )
        if not project_completed:
            attrs["placement_status"] = (
                Student.PlacementStatus.PROJECT_NOT_COMPLETED
            )
        elif placement_status == Student.PlacementStatus.PROJECT_NOT_COMPLETED:
            raise serializers.ValidationError({
                "placement_status": (
                    "Project is completed. Please select another placement status."
                )
            })

        return attrs
    

class BatchSwitchSerializer(serializers.Serializer):
    new_batch = serializers.PrimaryKeyRelatedField(
        queryset=Batch.objects.all()
    )
    reason = serializers.CharField(
        required=False,
        allow_blank=True
    )
    

class BatchSwitchHistorySerializer(serializers.ModelSerializer):
    previous_batch = serializers.StringRelatedField()
    new_batch = serializers.StringRelatedField()
    switched_by = serializers.StringRelatedField()

    class Meta:
        model = BatchSwitchHistory
        fields = [
            "id",
            "previous_batch",
            "new_batch",
            "reason",
            "switched_by",
            "switched_at",
        ]