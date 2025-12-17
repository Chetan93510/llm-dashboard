"""
Management command to generate sample LLM request data.

Usage:
    python manage.py generate_sample_data
    python manage.py generate_sample_data --count 100
    python manage.py generate_sample_data --days 30
"""

import random
import uuid
from datetime import timedelta
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.utils import timezone

from llm.models import LLMRequestLog, UserFeedback, AlertRule


class Command(BaseCommand):
    help = 'Generate sample LLM request data for testing'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--count',
            type=int,
            default=500,
            help='Number of sample requests to generate (default: 500)'
        )
        parser.add_argument(
            '--days',
            type=int,
            default=30,
            help='Number of days to spread data across (default: 30)'
        )
        parser.add_argument(
            '--error-rate',
            type=float,
            default=0.05,
            help='Proportion of error requests (default: 0.05)'
        )
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing data before generating new data'
        )
    
    def handle(self, *args, **options):
        count = options['count']
        days = options['days']
        error_rate = options['error_rate']
        
        if options['clear']:
            self.stdout.write('Clearing existing data...')
            LLMRequestLog.objects.all().delete()
            UserFeedback.objects.all().delete()
            self.stdout.write(self.style.SUCCESS('  Data cleared'))
        
        self.stdout.write(f'Generating {count} sample requests over {days} days...')
        
        models = [
            'llama-3.3-70b-versatile',
            'llama-3.1-8b-instant',
        ]
        
        error_types = ['timeout', 'rate_limit', 'provider_error', 'network']
        
        sample_prompts = [
            "Explain the concept of machine learning.",
            "Write a Python function to sort a list.",
            "What are the benefits of cloud computing?",
            "Summarize the key points of neural networks.",
            "How do I optimize database queries?",
            "Explain REST API best practices.",
            "What is the difference between SQL and NoSQL?",
            "Write a regex for email validation.",
            "Explain containerization with Docker.",
            "What are microservices architecture patterns?",
        ]
        
        sample_responses = [
            "Machine learning is a subset of artificial intelligence...",
            "Here's a Python sorting function using quicksort...",
            "Cloud computing offers several benefits including scalability...",
            "Neural networks are computational models inspired by...",
            "To optimize database queries, consider indexing...",
            "REST API best practices include proper versioning...",
            "SQL databases are relational while NoSQL databases...",
            "Here's a comprehensive email validation regex...",
            "Docker containerization involves packaging applications...",
            "Microservices architecture patterns include API Gateway...",
        ]
        
        users = ['user_001', 'user_002', 'user_003', 'user_004', 'user_005', None]
        
        now = timezone.now()
        created_logs = []
        
        for i in range(count):
            # Random timestamp within the time range
            random_offset = random.randint(0, days * 24 * 60)  # minutes
            timestamp = now - timedelta(minutes=random_offset)
            
            # Random model
            model = random.choice(models)
            
            # Determine if this is an error
            is_error = random.random() < error_rate
            
            # Generate token counts
            prompt_tokens = random.randint(10, 500)
            completion_tokens = random.randint(50, 1000) if not is_error else 0
            total_tokens = prompt_tokens + completion_tokens
            
            # Generate latency (errors tend to be faster due to early termination)
            if is_error:
                latency = random.randint(100, 2000)
            else:
                latency = random.randint(200, 5000)
            
            # Calculate cost
            pricing = {
                'llama-3.3-70b-versatile': {'input': 0.59, 'output': 0.79},
                'llama-3.1-8b-instant': {'input': 0.05, 'output': 0.08},
            }
            
            model_pricing = pricing.get(model, {'input': 0.50, 'output': 0.50})
            cost = Decimal(str(
                (prompt_tokens / 1_000_000) * model_pricing['input'] +
                (completion_tokens / 1_000_000) * model_pricing['output']
            ))
            
            log = LLMRequestLog(
                request_id=uuid.uuid4(),
                user_id=random.choice(users),
                model_name=model,
                prompt_text=random.choice(sample_prompts),
                response_text=random.choice(sample_responses) if not is_error else None,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=total_tokens,
                latency_ms=latency,
                cost_estimate=cost,
                status='error' if is_error else 'success',
                error_type=random.choice(error_types) if is_error else 'none',
                error_message='Sample error message for testing' if is_error else None,
                timestamp=timestamp,
            )
            created_logs.append(log)
            
            if (i + 1) % 100 == 0:
                self.stdout.write(f'  Generated {i + 1}/{count} requests...')
        
        # Bulk create for efficiency
        LLMRequestLog.objects.bulk_create(created_logs)
        
        self.stdout.write(self.style.SUCCESS(f'  Created {count} LLM request logs'))
        
        # Generate some feedback
        success_logs = LLMRequestLog.objects.filter(status='success')[:50]
        feedback_count = 0
        
        for log in success_logs:
            if random.random() < 0.3:  # 30% chance of feedback
                UserFeedback.objects.create(
                    request=log,
                    rating=random.choice(['thumbs_up', 'thumbs_up', 'thumbs_up', 'thumbs_down']),
                    comment=random.choice([None, 'Great response!', 'Could be better', 'Very helpful']),
                    user_id=log.user_id,
                )
                feedback_count += 1
        
        self.stdout.write(self.style.SUCCESS(f'  Created {feedback_count} feedback entries'))
        
        # Create default alert rules
        self.stdout.write('Creating default alert rules...')
        from llm.alerts import alert_service
        created_rules = alert_service.create_default_rules()
        self.stdout.write(self.style.SUCCESS(f'  Created {len(created_rules)} alert rules'))
        
        self.stdout.write(self.style.SUCCESS('\nSample data generation complete!'))
