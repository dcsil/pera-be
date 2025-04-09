from rest_framework.views import APIView
from django.http import JsonResponse


class index(APIView):
    def get(self, request):
        return JsonResponse({"message": "Hello world from Django"})
