# using SendGrid's Python Library (https://github.com/sendgrid/sendgrid-python)
import sendgrid
from sendgrid.helpers.mail import Mail
from ..credentials import SENDGRID_API_KEY, EMAIL

# custom function to send mail via SendGrid 
def sendGridMail(customer_email, email_subject, statement):
    print("INSIDE SENDMAIL FUNCTION")

    # create e-mail instance
    message = Mail(from_email=EMAIL,
                   to_emails=EMAIL,
                   subject=email_subject,
                   html_content=statement)
    
    # attempt to send email
    try:
        sg = sendgrid.SendGridAPIClient(api_key=SENDGRID_API_KEY)
        response = sg.send(message)
        print(response.status_code)
        print(response.body)
        print(response.headers)
    
    # print errors
    except Exception as e:
        print(str(e))