from django.utils import timezone
from ..models import ReservationLog, FoodLog

# called in middleware.py to ensure availability and reservation status are up to date
def check_statuses():
    curr_datetime = timezone.now()

    # if curr_quantity is 0, change status to unavailable
    FoodLog.objects.filter(avail_status='available', curr_quantity=0).update(avail_status='unavailable')
    # if expiry date < today's datetime, change status to expired
    FoodLog.objects.filter(avail_status='available', expiry_date__lt=curr_datetime).update(avail_status='expired')

    # gets all open reservations which have a collection time < today's datetime (i.e. expired)
    expired_reservations = ReservationLog.objects.filter(res_status='open', collection_date_time__lt=curr_datetime)
    
    for reservation in expired_reservations:
        # set the reservation to expired
        reservation.res_status = 'expired'
        
        # get the original item instance
        food_item = reservation.item
        
        if food_item:
            # add the quantity back to the food item
            food_item.curr_quantity += reservation.quantity
            # save the updated food item
            food_item.save()
        
        # save the updated reservation
        reservation.save()

    # update reservations that are expired (just in case)
    ReservationLog.objects.filter(res_status='open', collection_date_time__lt=curr_datetime).update(res_status='expired')