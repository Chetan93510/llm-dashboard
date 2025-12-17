"""
Management command to check alert rules.

Usage:
    python manage.py check_alerts
    python manage.py check_alerts --time-window 120
    python manage.py check_alerts --create-defaults
"""

from django.core.management.base import BaseCommand, CommandError

from llm.alerts import alert_service


class Command(BaseCommand):
    help = 'Check all active alert rules and trigger notifications'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--time-window',
            type=int,
            default=60,
            help='Time window in minutes for metric calculation (default: 60)'
        )
        parser.add_argument(
            '--create-defaults',
            action='store_true',
            help='Create default alert rules if none exist'
        )
    
    def handle(self, *args, **options):
        time_window = options['time_window']
        
        if options['create_defaults']:
            self.stdout.write('Creating default alert rules...')
            created_rules = alert_service.create_default_rules()
            
            if created_rules:
                for rule in created_rules:
                    self.stdout.write(
                        self.style.SUCCESS(f'  Created: {rule.name}')
                    )
            else:
                self.stdout.write('  No new rules created (already exist)')
        
        self.stdout.write(f'Checking alerts (time window: {time_window} minutes)...')
        
        try:
            triggered_alerts = alert_service.check_all_alerts(
                time_window_minutes=time_window
            )
            
            if triggered_alerts:
                self.stdout.write(
                    self.style.WARNING(f'\n{len(triggered_alerts)} alert(s) triggered:')
                )
                for alert in triggered_alerts:
                    self.stdout.write(f'  - {alert.alert_rule.name}: {alert.message}')
            else:
                self.stdout.write(
                    self.style.SUCCESS('\nNo alerts triggered. All metrics within thresholds.')
                )
                
        except Exception as e:
            raise CommandError(f'Error checking alerts: {e}')
