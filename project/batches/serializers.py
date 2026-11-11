from rest_framework import serializers
from students.models import Batch


class BatchSerializer(serializers.ModelSerializer):

    class Meta:
        model = Batch
        fields = [
            "id",
            "course",
            "month",
            "year",
            "batch_number",
        ]
        read_only_fields = ["id"]