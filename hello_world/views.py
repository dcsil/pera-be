from rest_framework.views import APIView
from rest_framework.response import Response

class index(APIView):
    def get(self, request):
        return Response("Hello world from Django")
