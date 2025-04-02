from rest_framework import permissions, serializers, views
from drf_spectacular.utils import extend_schema
from knox.auth import TokenAuthentication


class DefaultErrorResponseSerializer(serializers.Serializer):
    """Default format of response when raising most APIException classes"""

    detail = serializers.CharField()


def _extend_responses(f):
    # see https://github.com/tfranzel/drf-spectacular/blob/master/drf_spectacular/utils.py
    BaseSchema = getattr(f, "kwargs", {}).get("schema", None)
    if BaseSchema:

        class ExtendedSchema(BaseSchema):
            def get_response_serializers(self):
                d = super().get_response_serializers()
                # let's not touch it if there's already some spec
                if 401 not in d:
                    d[401] = DefaultErrorResponseSerializer
                return d

        f.kwargs["schema"] = ExtendedSchema
        return f
    return extend_schema(responses={401: DefaultErrorResponseSerializer})(f)


def extend_schema_auth_failed(cls):
    """Decorator. You're probably looking for require_authentication."""
    if not issubclass(cls, views.APIView):
        raise ValueError(str(cls) + " is not a rest_framework.views.APIView")
    for meth in views.APIView.http_method_names:
        if hasattr(cls, meth):
            setattr(cls, meth, _extend_responses(getattr(cls, meth)))
    return cls


def require_authentication(cls):
    """Adds authentication to an APIView. Put it above @extend_schema_view"""
    cls = extend_schema_auth_failed(cls)

    class Decorator(cls):
        authentication_classes = (TokenAuthentication,)
        permission_classes = (permissions.IsAuthenticated,)

    return Decorator
