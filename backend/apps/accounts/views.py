from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers, viewsets, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import User


class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=False)
    administrator = serializers.BooleanField(read_only=True)

    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "email",
            "first_name",
            "last_name",
            "role",
            "is_active",
            "administrator",
            "password",
        ]

    def validate_password(self, value):
        validate_password(value, self.instance)
        return value

    def create(self, data):
        if not data.get("password"):
            raise serializers.ValidationError({"password": "Define una contraseña."})
        return User.objects.create_user(**data)

    def update(self, instance, data):
        password = data.pop("password", None)
        instance = super().update(instance, data)
        if password:
            instance.set_password(password)
            instance.save()
        return instance


class AdminOnly(permissions.BasePermission):
    def has_permission(self, request, view):
        return bool(request.user.is_authenticated and request.user.administrator)


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all().order_by("id")
    serializer_class = UserSerializer
    permission_classes = [AdminOnly]
    http_method_names = ["get", "post", "patch", "head", "options"]

    @action(
        detail=False,
        methods=["get", "patch"],
        permission_classes=[permissions.IsAuthenticated],
    )
    def me(self, request):
        if request.method == "PATCH":
            allowed = {
                k: v
                for k, v in request.data.items()
                if k in ["first_name", "last_name", "email", "password"]
            }
            s = self.get_serializer(request.user, data=allowed, partial=True)
            s.is_valid(raise_exception=True)
            s.save()
        return Response(self.get_serializer(request.user).data)
