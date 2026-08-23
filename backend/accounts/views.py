from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken, TokenError
from .serializers import UserSerializer
class MeView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request): return Response(UserSerializer(request.user).data)
class LogoutView(APIView):
    def post(self, request):
        try: RefreshToken(request.data["refresh"]).blacklist()
        except (KeyError, TokenError): pass
        return Response(status=204)

