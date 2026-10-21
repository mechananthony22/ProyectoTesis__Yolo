from django.core.exceptions import ValidationError
from django.db.models import ProtectedError
from rest_framework.views import exception_handler as drf_handler
from rest_framework.response import Response


def exception_handler(exc, context):
    if isinstance(exc, ValidationError):
        return Response({"detail": exc.messages}, status=400)
    if isinstance(exc, ProtectedError):
        return Response(
            {
                "detail": "Este registro está vinculado a evidencias; no puede eliminarse."
            },
            status=409,
        )
    return drf_handler(exc, context)
