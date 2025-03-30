from django.core.serializers import serialize
from django.utils import timezone
from twilio.rest import Client
from .send_email import *
from .helper_functions import haversine
from ..credentials import TWILIO_AUTH_TOKEN, TWILIO_SID, PHONE_NUMBER, TWILIO_PHONE_NUMBER
from ..models import CustomerInfo
from ..simple_task import *
import json

# connect to Twilio to send SMSes
client = Client(TWILIO_SID, TWILIO_AUTH_TOKEN)

# send SMS to customer
def send_sms(name, phone_number, sms_message):
    # create message
    greeting = f"Hi {name}!"
    message = greeting + sms_message
    
    # sms sending logic (intentionally commented out)
    print(f"Sending SMS to {name}", timezone.now())
    # WORKING
    client.messages.create(from_=TWILIO_PHONE_NUMBER,  # Twilio-provided number
                           body=message,
                           to=PHONE_NUMBER)  # replace with database if numbers are vefified

# send email to customer
def send_email(name, email, email_message):
    # create message
    greeting = f"Hi {name}!"
    message = greeting + email_message

    # email sending logic (intentionally commented out)
    print(f"Sending email to {name}", timezone.now())
    # WORKING
    sendGridMail('charu.sgp@gmail.com', 'New offers have arrived!', message)

# convert customer data to JSON for processing of data in Celery
def convert_to_json(customer_list):
    customer_json = []
    for customer in customer_list:
        customer_data = {"first_name": customer.first_name,
                          "phone_number": str(customer.phone_number),
                          "email": customer.email,
                          "sms_alert": customer.sms_alert,
                          "email_alert": customer.email_alert}
        
        customer_json.append(customer_data)

    return customer_json

# convert model objects to JSON for processing of data in Celery
def model_to_json(instance):
    json_data = serialize('json', [instance])
    data = json.loads(json_data)[0]
    data['fields']['id'] = data['pk']  # add primary key manually
    return data['fields']

# gets the relevant customers for alert based on distance band
def get_relevant_customers_for_alert(customers, business_profile):
    customers = CustomerInfo.objects.all()
    customers_within_3km = []
    customers_within_5km = []
    customers_within_10km = []

    for customer in customers:
        within_range, distance = haversine(customer.lat, customer.long, business_profile.lat, business_profile.long, 10)
        if within_range:
            # check if its between 0 and 3km
            if distance <= 3 and customer.alert_radius >= 3 and (customer.sms_alert or customer.email_alert):
                customers_within_3km.append(customer)
                print(customer.first_name, distance, "put into 3km")

            # check if its between 3 and 5km
            elif distance > 3 and distance <= 5 and customer.alert_radius >= 5 and (customer.sms_alert or customer.email_alert):
                customers_within_5km.append(customer)
                print(customer.first_name, "put into 5km")

            # check if its between 5 and 10km
            elif distance > 5 and distance <= 10 and customer.alert_radius >= 10 and (customer.sms_alert or customer.email_alert):
                customers_within_10km.append(customer)
                print(customer.first_name, "put into 10km")

            else:
                # print for logging
                print(customer.first_name, distance, "within range but not categorised")

        else:
            # print for logging
            print(customer.first_name, distance, "is more than 10km")

    return customers_within_3km, customers_within_5km, customers_within_10km

# create SMS and email statements
def create_alert_statement(json_data, business_profile):
    statements = [
        f"{item['quantity']} {item['units']} of {item['food_item']} for ${item['price_per_unit']} [Quantity: {item['curr_quantity']}]"
        for item in json_data
    ]

    res = '\n    - '.join(statements)

    # SMS statement
    sms_statement = f'''
These deals have just come in, reserve them before they are gone!
    - {res}

Location: {business_profile['business_name']}, {business_profile['address']}
Reserve here: http://127.0.0.1:8080/customer/reservation/make/?business_id={business_profile['id']}
    '''

    # Email statement
    email_statement = f'''
                        <br>These deals have just come in, reserve them before they are gone!
                        <ul>
                            {''.join([f'<li>{statement}</li>' for statement in statements])}
                        </ul>
                        <br>Location: {business_profile['business_name']}, {business_profile['address']}
                        <br>Reserve <a href="http://127.0.0.1:8080/customer/reservation/make/?business_id={business_profile['id']}">Here</a>
                    '''

    return sms_statement, email_statement
