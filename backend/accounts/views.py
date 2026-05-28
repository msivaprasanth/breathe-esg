from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.permissions import AllowAny
from django.contrib.auth import authenticate

from ingestion.models import TenantMembership
from ingestion.serializers import UserSerializer


class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        username = request.data.get('username')
        password = request.data.get('password')

        user = authenticate(username=username, password=password)

        if not user:
            return Response(
                {'error': 'Invalid credentials.'},
                status=401
            )

        token, _ = Token.objects.get_or_create(user=user)

        membership = (
            TenantMembership.objects
            .filter(user=user)
            .select_related('tenant')
            .first()
        )

        return Response({
            'token': token.key,
            'user': UserSerializer(user).data,
            'tenant': {
                'id': str(membership.tenant.id),
                'name': membership.tenant.name,
                'slug': membership.tenant.slug,
                'role': membership.role,
            } if membership else None,
        })


class MeView(APIView):

    def get(self, request):

        membership = (
            TenantMembership.objects
            .filter(user=request.user)
            .select_related('tenant')
            .first()
        )

        return Response({
            'user': UserSerializer(request.user).data,
            'tenant': {
                'id': str(membership.tenant.id),
                'name': membership.tenant.name,
                'slug': membership.tenant.slug,
                'role': membership.role,
            } if membership else None,
        })