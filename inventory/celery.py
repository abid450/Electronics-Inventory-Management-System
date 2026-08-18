import os
from celery import Celery
from celery.schedules import crontab


os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'inventory.settings')

app = Celery('inventory')

app.config_from_object('django.conf:settings', namespace='CELERY')

app.autodiscover_tasks()

# Debug Task --------------------------------------------------------
@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')
    return f'Task executed successfully with id: {self.request.id}'



# Periodic tasks (Celery Beat)
app.conf.beat_schedule = {
    # ... existing schedules ...
    
    'check_and_notify_low_stock': {
        'task': 'stock_alert.tasks.check_and_notify_low_stock',
        'schedule': crontab(minute='*/15'),  # Every 15 minutes
        'options': {
            'expires': 600,  # 10 minutes
            'queue': 'default',
        },

        # Send pending payment reminders (optional)
    'send-pending-reminders': {
        'task': 'stock_alert.tasks.send_pending_reminder',
        'schedule': crontab(hour=10, minute=0),  # সকাল ১০টা
        'options': {
            'expires': 1800,
        },
    },
    },


   
    
}

# Task routes (বিভিন্ন queue তে পাঠানোর জন্য)
app.conf.task_routes = {
    
    'stock_alert.tasks.check_low_stock': {'queue': 'default'},
    'stock_alert.tasks.check_and_notify_low_stock': {'queue': 'default'},
    'stock_alert.tasks.send_low_stock_email': {'queue': 'email'},
    'stock_alert.tasks.send_payment_confirmation_email': {'queue': 'email'},
    'stock_alert.tasks.send_pending_reminder': {'queue': 'email'},


}

# ============================================================
# TASK QUEUES
# ============================================================

app.conf.task_queues = {
    'default': {
        'exchange': 'default',
        'routing_key': 'default',
    },
    'email': {
        'exchange': 'email',
        'routing_key': 'email',
    },

    'low_priority': {
        'exchange': 'low_priority',
        'routing_key': 'low_priority',
        'exchange_type': 'direct',
    },
}


# ============================================================
# TASK SETTINGS
# ============================================================

app.conf.task_time_limit = 30 * 60  # 30 minutes
app.conf.task_soft_time_limit = 25 * 60  # 25 minutes
app.conf.task_max_retries = 3
app.conf.task_default_retry_delay = 60  # 1 minute
app.conf.task_acks_late = True
app.conf.task_track_started = True
app.conf.task_send_sent_event = True