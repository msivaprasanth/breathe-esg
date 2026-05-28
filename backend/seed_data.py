import os
import sys
import django

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'breathe_esg.settings')

django.setup()

from django.contrib.auth.models import User
from rest_framework.authtoken.models import Token
from ingestion.models import Tenant, TenantMembership

# Create tenant
tenant, _ = Tenant.objects.get_or_create(
    slug='acme-corp',
    defaults={
        'name': 'Acme Corporation'
    }
)

users = [
    ('admin', 'admin123', 'admin'),
    ('analyst1', 'analyst123', 'analyst'),
    ('analyst2', 'analyst456', 'analyst'),
]

for username, password, role in users:

    user, created = User.objects.get_or_create(
        username=username,
        defaults={
            'email': f'{username}@acme.com',
            'first_name': username.capitalize(),
        }
    )

    user.set_password(password)
    user.save()

    Token.objects.get_or_create(user=user)

    TenantMembership.objects.get_or_create(
        user=user,
        tenant=tenant,
        defaults={
            'role': role
        }
    )

    print(f'Created: {username}')

print('Done.')
