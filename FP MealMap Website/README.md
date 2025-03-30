# mealmap

PROJECT TITLE: MealMap

PROJECT DESCRIPTION: MealMap is a Django-based web application that helps small food businesses reduce waste by notifying customers (in a multi-tiered manner) about discounted or free expiring food via SMS and email alerts.

INSTALLATION INSTRUCTIONS
1. Navigate to the root directory of the application
2. Install required modules: pip install -r requirements.txt

ENVIRONMENT SETUP
- Operating System: macOS
- Python Version: 3.9.6

ENSURE MIGRATIONS ARE DONE
- python manage.py makemigrations
- python manage.py showmigrations (to view migrations)
- python manage.py migrate (for future migrations)

TO VIEW DATABASE (ensure directory is set to root directory)
- /Library/PostgreSQL/17/bin/psql -h localhost -d postgres
- Password: charucoal123
- To choose database: \c mealmap_db
- To view tables: \dt

SETTING UP THE APPLICATION (ensure directory is set to 'FP MealMap Website/mealmap/webdata')
- Run '/usr/local/bin/redis-server' in a new terminal (sets up Redis server)
- Run 'celery -A webdata.simple_task.celery_app worker --loglevel=info' in another new terminal (sets up Celery)

Note: to make use of the SMS, Email, Account Registration and Profile Update functionalities, you have to:
1. Rename .env.example file to .env
2. Add the relevant API details
3. Uncomment the code section in views.py labelled as 'ASYNC COMMENTED OUT FOR NOW, UNCOMMENT WHEN NEEDED'
4. Ensure your device has internet access

RUNNING THE APPLICATION (ensure directory is set to 'FP MealMap Website/mealmap/webdata')
- Run 'python manage.py runserver 127.0.0.1:8080' in another new terminal
- Access web application via http://127.0.0.1:8080

ACCESSING API DOCUMENTATION
- Access via http://127.0.0.1:8080/api/schema/redoc

LOGIN CREDENTIALS FOR DJANGO ADMIN SITE (access via http://127.0.0.1:8080/admin/)
Username: admin
Password: django123

ACCESS API Endpoints (need to first login as admin via Django-admin site)
After logging in as admin:
- http://127.0.0.1:8080/api (view all APIs)
- http://127.0.0.1:8080/api/schema/ (download schema in YAML format)
- http://127.0.0.1:8080/api/schema/swagger-ui (API endpoints via Swagger)

DEPENDENCIES - Can be viewed in the requirements.txt file

DEMO VIDEO: 