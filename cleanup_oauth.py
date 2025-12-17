import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from allauth.socialaccount.models import SocialApp

# Delete ALL social apps from database - we'll use settings.py config only
print('Removing ALL SocialApp entries from database...')
count = SocialApp.objects.all().count()
SocialApp.objects.all().delete()
print(f'Deleted {count} apps from database')
print('\nGoogle OAuth will now use settings.py configuration only.')
print('Done!')
