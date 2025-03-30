from django.core.exceptions import ValidationError
from django.contrib.auth.models import AbstractUser
from django_countries.fields import CountryField
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from datetime import timedelta
from phonenumber_field.modelfields import PhoneNumberField

# CUSTOMER INFORMATION TABLE
class CustomerInfo(models.Model):
    ALERT_RADIUS_CHOICES = [
        (3, '3KM'),
        (5, '5KM'),
        (10, '10KM'),
    ]

    customer_id = models.AutoField(primary_key=True)
    first_name = models.CharField(max_length=255)
    middle_name = models.CharField(max_length=255, blank=True, null=True)
    last_name = models.CharField(max_length=255)
    date_of_birth = models.DateField()
    country = CountryField(blank_label="Select a country")
    phone_number = PhoneNumberField()
    email = models.EmailField(unique=True)
    address = models.TextField()
    long = models.FloatField()
    lat = models.FloatField()
    alert_radius = models.IntegerField(choices=ALERT_RADIUS_CHOICES, default=3)
    sms_alert = models.BooleanField(default=True)
    email_alert = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.first_name + " " + self.last_name + f" ({self.user.username})"

# BUSINESS INFORMATION TABLE
class BusinessInfo(models.Model):
    business_id = models.AutoField(primary_key=True)
    business_name = models.CharField(max_length=255)
    description = models.TextField()
    country = CountryField(blank_label="Select a country")
    address = models.TextField()
    long = models.FloatField(default=1)
    lat = models.FloatField(default=1)
    phone_number = PhoneNumberField()
    email = models.EmailField(unique=True)
    opening_time = models.TimeField()
    closing_time = models.TimeField()
    verified = models.BooleanField(default=False)
    business_image = models.ImageField(upload_to='business/', null=True, blank=True, default='business/default.jpg')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        # if no image set, reverts to default
        if not self.business_image:
            self.business_image = self._meta.get_field('business_image').get_default()

        self.clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.business_name + f" ({self.user.username})"

# USER CREDENTIALS TABLE
class CustomUser(AbstractUser):
    ACCOUNT_TYPE_CHOICES = [
        ('customer', 'Customer'),
        ('business', 'Business'),
        ('admin', 'Admin')
    ]

    account_type = models.CharField(max_length=10, choices=ACCOUNT_TYPE_CHOICES)

    # foreign keys for linking to customer or business profile
    customer = models.OneToOneField(CustomerInfo, on_delete=models.CASCADE, null=True, blank=True, related_name='user')
    business = models.OneToOneField(BusinessInfo, on_delete=models.CASCADE, null=True, blank=True, related_name='user')

    def save(self, *args, **kwargs):
        # ensure only one of customer or business is set based on account_type
        if self.account_type == 'customer' and self.business:
            self.business = None
        elif self.account_type == 'business' and self.customer:
            self.customer = None
        super().save(*args, **kwargs)

# DIETARY OPTIONS TABLE (FOR BUSINESSES)
class DietaryReg(models.Model):
    DIETARY_CHOICES = [
        ('vegetarian', 'Vegetarian'),
        ('vegan', 'Vegan'),
        ('kosher', 'Kosher'),
        ('halal', 'Halal'),
        ('jain', 'Jain'),
        ('glutenfree', 'Gluten-free')
    ]

    dietary_id = models.AutoField(primary_key=True)
    business = models.ForeignKey(BusinessInfo, on_delete=models.CASCADE, related_name='dietary_preferences')
    dietary_opt = models.CharField(choices=DIETARY_CHOICES, default=3)

    class Meta:
        unique_together = ('business', 'dietary_opt')

    def __str__(self):
        return f"Business ID {self.business.business_id} caters to {self.dietary_opt.capitalize()}"

# FOOD LOG TABLE (FOR BUSINESSES)
class FoodLog(models.Model):
    AVAIL_STATUS = [('available', 'Available'),
                    ('unavailable', 'Unavailable'),
                    ('expired', 'Expired')]

    item_id = models.AutoField(primary_key=True)
    business = models.ForeignKey(BusinessInfo, on_delete=models.CASCADE, related_name="food_items")
    food_item = models.CharField(max_length=255)
    quantity = models.IntegerField()
    total_units = models.IntegerField()
    curr_quantity = models.IntegerField()
    price_per_unit = models.FloatField()
    units = models.CharField(max_length=50)
    expiry_date = models.DateTimeField()
    avail_status = models.CharField(max_length=50, choices=AVAIL_STATUS, default='available')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"[ID: {self.item_id}] {self.food_item} - {self.quantity} {self.units} at {self.price_per_unit}/unit, Expiry: {self.expiry_date.strftime('%Y-%m-%d %H:%M:%S')}, Status: {self.avail_status}"

    def clean(self):
        if self.quantity < 1 or self.total_units < 1:
            raise ValidationError("Value cannot be less than 1.")

        # extract date and ensure its greater than today's date
        if self.expiry_date < timezone.now() + timedelta(days=1):
            raise ValidationError("Expiry date must be at least 24 hours in the future.")
    
    def save(self, *args, **kwargs):
        # check if curr_quantity is 0 and update avail_status to 'unavailable'
        if self.curr_quantity == 0:
            self.avail_status = 'unavailable'
        # check if the current date is greater than expiry_date and update avail_status to 'expired'
        elif self.expiry_date < timezone.now():
            self.avail_status = 'expired'
        else:
            self.avail_status = 'available'  # set to available if neither of the above conditions are met

        if self._state.adding:
            self.curr_quantity = self.total_units

        super().save(*args, **kwargs)

# PURCHASE LOG TABLE (FOR CUSTOMERS)
class PurchaseLog(models.Model):
    purchase_id = models.AutoField(primary_key=True)
    date_purchased = models.DateTimeField(default=timezone.now)
    item = models.ForeignKey(FoodLog, on_delete=models.CASCADE)
    customer = models.ForeignKey(CustomerInfo, on_delete=models.CASCADE)
    quantity = models.IntegerField()

    def __str__(self):
        return f"[ID: {self.purchase_id}] - {self.quantity} of item ID {self.item.item_id} purchased by {self.customer} on {self.date_purchased.strftime('%Y-%m-%d %H:%M:%S')}"

# RESERVATION LOG TABLE (FOR CUSTOMERS)
class ReservationLog(models.Model):
    RES_STATUS = [
        ('open', 'Open'),
        ('collected', 'Collected'),
        ('expired', 'Expired')
    ]

    res_id = models.AutoField(primary_key=True)
    item = models.ForeignKey(FoodLog, on_delete=models.CASCADE, related_name="reservations")
    customer = models.ForeignKey(CustomerInfo, on_delete=models.CASCADE)
    quantity = models.IntegerField()
    reservation_date_time = models.DateTimeField(default=timezone.now)
    res_status = models.CharField(max_length=10, choices=RES_STATUS, default='open')
    collection_date_time = models.DateTimeField()

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['item', 'customer'],
                condition=models.Q(res_status='open'),
                name='unique_available_reservation'
            )
        ]

    def save(self, *args, **kwargs):
        # set collection_date_time only when creating a new reservation
        if self._state.adding:
            self.collection_date_time = self.reservation_date_time + timedelta(minutes=20)

        # update status to 'expired' if past collection time and not collected
        if timezone.now() > self.collection_date_time and self.res_status == 'open':
            self.res_status = 'expired'

        super().save(*args, **kwargs)

    def __str__(self):
        return f"Reservation by {self.customer} for {self.quantity} of item ID {self.item.item_id}"
