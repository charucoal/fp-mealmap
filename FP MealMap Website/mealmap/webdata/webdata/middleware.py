from django.utils.deprecation import MiddlewareMixin
from webdata.custom_functions.check_data import check_statuses

class StatusCheckMiddleware(MiddlewareMixin):
    def process_request(self, request):
        check_statuses()  # run the status check for reservations and items before any view logic