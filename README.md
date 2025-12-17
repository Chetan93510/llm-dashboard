# LLM Observability Dashboard

A production-grade observability dashboard for monitoring and analyzing LLM API calls in real-time. Built with Django + Django REST Framework backend and HTML + CSS + Vanilla JavaScript frontend.

![Dashboard Overview](https://via.placeholder.com/800x400?text=LLM+Observability+Dashboard)

## Features

- **Real-time LLM Call Logging** - Automatically logs all LLM API requests with comprehensive metadata
- **Token Usage Tracking** - Monitor prompt and completion token usage across models
- **Latency Monitoring** - Track average and P95 latency per model
- **Cost Estimation** - Automatic cost calculation based on token usage
- **Error Tracking** - Categorized error tracking with detailed messages
- **User Feedback System** - Collect thumbs up/down ratings for LLM responses
- **Alerting System** - Configurable alerts for error rate, latency, and token spikes
- **Interactive Dashboard** - Beautiful charts and visualizations with Chart.js
- **Data Export** - Export analytics as CSV or JSON

## Tech Stack

- **Backend**: Django 5.0+, Django REST Framework
- **Database**: SQLite (dev) / PostgreSQL (prod)
- **Frontend**: HTML, Tailwind CSS (CDN), Vanilla JavaScript, Chart.js
- **LLM Provider**: Groq API

## Quick Start

### 1. Clone and Setup

```bash
# Navigate to project directory
cd "LLM Observability Dashboard"

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
# Copy environment template
cp .env.example .env

# Edit .env and add your Groq API key
# GROQ_API_KEY=your-groq-api-key-here
```

### 3. Initialize Database

```bash
# Run migrations
python manage.py migrate

# Create superuser for admin access
python manage.py createsuperuser

# (Optional) Generate sample data for testing
python manage.py generate_sample_data --count 500
```

### 4. Run the Server

```bash
python manage.py runserver
```

Visit [http://localhost:8000](http://localhost:8000) to access the dashboard.

## Project Structure

```
llm_observability_dashboard/
├── core/                   # Django project settings
│   ├── settings.py         # Configuration with env variables
│   ├── urls.py            # Main URL routing
│   └── wsgi.py            # WSGI application
├── llm/                    # Main Django app
│   ├── models.py          # Database models
│   ├── serializers.py     # DRF serializers
│   ├── views.py           # API views
│   ├── urls.py            # API URL routing
│   ├── services.py        # Groq LLM service wrapper
│   ├── metrics.py         # Metrics aggregation service
│   ├── alerts.py          # Alerting system
│   ├── admin.py           # Django admin configuration
│   └── management/
│       └── commands/
│           ├── check_alerts.py      # Alert checking command
│           └── generate_sample_data.py  # Sample data generator
├── templates/              # HTML templates
│   ├── base.html          # Base template with navigation
│   ├── index.html         # Overview dashboard
│   ├── analytics.html     # Detailed analytics
│   ├── logs.html          # Request logs browser
│   ├── feedback.html      # User feedback page
│   └── alerts.html        # Alerts management
├── static/                 # Static files
├── logs/                   # Application logs
├── requirements.txt        # Python dependencies
├── .env.example           # Environment variables template
└── README.md              # This file
```

## API Endpoints

### Metrics
- `GET /api/metrics/overview/` - Overview metrics (total calls, tokens, latency, error rate)
- `GET /api/metrics/token-usage/` - Token usage over time
- `GET /api/metrics/latency/` - Latency metrics by model
- `GET /api/metrics/errors/` - Error breakdown
- `GET /api/metrics/model-usage/` - Model usage statistics
- `GET /api/metrics/daily-stats/` - Daily statistics

### Logs
- `GET /api/logs/` - List all request logs (paginated, filterable)
- `GET /api/logs/<request_id>/` - Get single log details
- `GET /api/logs/errors/` - List error logs only

### Feedback
- `POST /api/feedback/` - Submit feedback for a request
- `GET /api/feedback/` - List all feedback
- `GET /api/feedback/analytics/` - Feedback analytics

### Alerts
- `GET /api/alerts/rules/` - List alert rules
- `POST /api/alerts/rules/` - Create alert rule
- `PUT /api/alerts/rules/<id>/` - Update alert rule
- `DELETE /api/alerts/rules/<id>/` - Delete alert rule
- `GET /api/alerts/logs/` - List triggered alerts
- `POST /api/alerts/logs/<id>/acknowledge/` - Acknowledge an alert

### Export
- `GET /api/export/csv/` - Export logs as CSV
- `GET /api/export/json/` - Export logs as JSON

### LLM
- `POST /api/llm/prompt/` - Send a prompt to the LLM (automatically logged)

## Using the LLM Service

The dashboard includes a Groq LLM service wrapper that automatically logs all requests:

```python
from llm.services import groq_service

# Send a prompt (automatically logged to database)
result = groq_service.complete(
    prompt="Explain machine learning in simple terms",
    model="llama-3.3-70b-versatile",  # optional
    user_id="user_123",  # optional
    max_tokens=1024,  # optional
    temperature=0.7,  # optional
)

print(result['response'])
print(f"Tokens used: {result['total_tokens']}")
print(f"Cost: ${result['cost_estimate']}")
```

## Alert Configuration

Create default alert rules:

```bash
python manage.py check_alerts --create-defaults
```

Run alert checks (can be scheduled with cron):

```bash
python manage.py check_alerts --time-window 60
```

### Alert Types

1. **Error Rate** - Triggers when error percentage exceeds threshold
2. **Latency** - Triggers when P95 latency exceeds threshold (ms)
3. **Token Spike** - Triggers when token usage is N times the previous period

## Query Parameters

Most endpoints support filtering:

- `start_date` - ISO format datetime
- `end_date` - ISO format datetime
- `model` - Filter by model name
- `status` - Filter by status (success/error)
- `group_by` - Grouping period (hour/day/month)

Example:
```
GET /api/metrics/token-usage/?start_date=2024-01-01T00:00:00Z&group_by=day&model=llama-3.3-70b-versatile
```

## Production Deployment

### Environment Variables

Set these for production:

```bash
DEBUG=False
DJANGO_SECRET_KEY=<generate-secure-key>
ALLOWED_HOSTS=your-domain.com
GROQ_API_KEY=<your-api-key>

# For PostgreSQL
DATABASE_URL=postgres://user:pass@host:5432/dbname

# For email alerts
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
ALERT_EMAIL_RECIPIENTS=admin@example.com
```

### Run with Gunicorn

```bash
pip install gunicorn
gunicorn core.wsgi:application --bind 0.0.0.0:8000
```

### Scheduled Alert Checks

Add to crontab (runs every 15 minutes):

```bash
*/15 * * * * /path/to/venv/bin/python /path/to/manage.py check_alerts
```

## Database Models

### LLMRequestLog
Stores all LLM API request data:
- `request_id` (UUID) - Unique identifier
- `user_id` - Optional user identifier
- `model_name` - LLM model used
- `prompt_text` / `response_text` - Request/response content
- `prompt_tokens` / `completion_tokens` / `total_tokens` - Token counts
- `latency_ms` - Request latency
- `cost_estimate` - Estimated cost in USD
- `status` - success/error
- `error_type` / `error_message` - Error details
- `timestamp` - Request time

### UserFeedback
- `request` (FK) - Related LLM request
- `rating` - thumbs_up/thumbs_down
- `comment` - Optional feedback text

### AlertRule
- `name` / `description` - Alert identification
- `metric_type` - error_rate/latency/token_spike
- `threshold` - Trigger threshold
- `is_active` - Enable/disable
- `notify_email` - Send email notifications

### AlertLog
- `alert_rule` (FK) - Related rule
- `message` - Alert message
- `metric_value` - Value that triggered alert
- `acknowledged` - Acknowledgment status

## Security Notes

- **API Keys**: Never hardcode API keys. Use environment variables.
- **CSRF**: Enabled by default for web forms.
- **CORS**: Configured for development. Restrict in production.
- **Debug Mode**: Disable in production.

## License

MIT License

## Contributing

Contributions are welcome! Please open an issue or submit a pull request.
