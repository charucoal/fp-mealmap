# using SendGrid's Python Library (https://github.com/sendgrid/sendgrid-python)
import sendgrid
from sendgrid.helpers.mail import Mail

# custom function to send mail via SendGrid 
def sendGridMail(customer_email, email_subject, statement):
    print("INSIDE SENDMAIL FUNCTION")

    # create e-mail instance
    message = Mail(from_email='charu.sgp@gmail.com',
                   to_emails=customer_email,
                   subject=email_subject,
                   html_content=statement)
    
    # attempt to send email
    try:
        sg = sendgrid.SendGridAPIClient(api_key='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')
        response = sg.send(message)
        print(response.status_code)
        print(response.body)
        print(response.headers)
    
    # print errors
    except Exception as e:
        print(str(e))