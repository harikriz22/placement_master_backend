from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from django.conf import settings
from rest_framework import serializers
from django.contrib.auth import authenticate


class MemberRegistrationSerializer(serializers.ModelSerializer):
    name = serializers.CharField(max_length=150,trim_whitespace=True)
    email = serializers.EmailField(max_length=254)
    password = serializers.CharField(write_only=True,min_length=8,trim_whitespace=False)
    invite_code = serializers.CharField(write_only=True,trim_whitespace=True)

    class Meta:
        model = User
        fields = ("name","email","password","invite_code",)

    def validate_name(self, value):
        if not value.strip():
            raise serializers.ValidationError(
                "Name cannot be empty."
            )

        return value.strip()

    def validate_email(self, value):
        email = value.strip().lower()

        if User.objects.filter(email__iexact=email).exists():
            raise serializers.ValidationError(
                "An account with this email already exists."
            )

        if User.objects.filter(username__iexact=email).exists():
            raise serializers.ValidationError(
                "An account with this email already exists."
            )

        return email

    def validate_invite_code(self, value):
        expected_code = getattr(
            settings,
            "PLACEMENT_INVITE_CODE",
            None
        )

        if not expected_code:
            raise serializers.ValidationError(
                "Registration is currently unavailable."
            )

        if value != expected_code:
            raise serializers.ValidationError(
                "Invalid invite code."
            )

        return value

    def validate_password(self, value):
        try:
            validate_password(value)

        except DjangoValidationError as error:
            raise serializers.ValidationError(error.messages)

        return value

    def create(self, validated_data):
        name = validated_data.pop("name")
        email = validated_data.pop("email")

        validated_data.pop("invite_code")

        password = validated_data.pop("password")

        return User.objects.create_user(
            username=email,
            email=email,
            first_name=name,
            password=password
        )
        
        
        
class LoginSerializer(serializers.Serializer):
    
    email = serializers.EmailField(required=True)
    password = serializers.CharField(write_only=True,required=True,trim_whitespace=False)

    def validate(self, attrs):
        email = attrs["email"].strip().lower()
        password = attrs["password"]
        request = self.context.get("request")

        user = authenticate(
            request=request,
            username=email,
            password=password
        )

        if user is None:
            raise serializers.ValidationError({
                "detail": "Invalid email or password."
            })

        attrs["user"] = user

        return attrs        
        

    