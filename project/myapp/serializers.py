from rest_framework import serializers
from .models import MasterStudent


class MasterStudentSerializer(serializers.ModelSerializer):

    class Meta:
        model = MasterStudent
        fields = '__all__'

        # Eligibility is calculated automatically in the model's save()
        read_only_fields = ['id', 'is_eligible']