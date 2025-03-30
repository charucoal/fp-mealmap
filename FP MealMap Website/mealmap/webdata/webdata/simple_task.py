from celery import Celery, shared_task
from celery.utils.log import get_task_logger
import os, django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "mealmap.settings")
django.setup()

# initialise celery
celery_app = Celery("webdata")
celery_app.config_from_object("django.conf:settings", namespace="CELERY")
celery_app.autodiscover_tasks()

logger = get_task_logger(__name__)
logger.info("This is a Celery task log")

# get the latest updated quantities of items
# and add them to statement to be sent via SMS or email
@shared_task(max_retries=0)
def get_latest_quantity(item_ids, business_profile):
    from webdata.custom_functions.queue_data import create_alert_statement, model_to_json
    from .models import FoodLog

    log_data = [model_to_json(FoodLog.objects.get(item_id=item_id))
                                for item_id in item_ids
                                if FoodLog.objects.get(item_id=item_id).curr_quantity > 0]
    
    if log_data == []:
        return []

    statements = create_alert_statement(log_data[:3], business_profile)
    return statements

# queue the alerts to be sent asynchronously
@shared_task(max_retries=0)
def queue_alerts(statements, customers_json):
    if not statements:
        return "No valid statements to process. Skipping alert queue." # early return, no alert will be sent

    from webdata.custom_functions.queue_data import send_sms, send_email
    
    logger.info("ALERTS ARE QUEUED")
    sms_statement = statements[0]
    email_statement = statements[1]

    # ALERTS SENT TO CUSTOMER VIA SMS AND/OR EMAIL
    for customer in customers_json:
        logger.info(customer)
        if customer["sms_alert"]:
            logger.info(f"Sending SMS to {customer['first_name']}")
            send_sms(customer["first_name"], customer["phone_number"], sms_statement)

        if customer["email_alert"]:
            logger.info(f"Sending Email to {customer['first_name']}")
            send_email(customer["first_name"], customer["email"], email_statement)