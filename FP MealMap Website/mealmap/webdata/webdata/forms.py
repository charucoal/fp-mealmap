from .models import *
from django import forms
from django.core.exceptions import ValidationError
from django.contrib.auth.forms import UserCreationForm
from django_countries.widgets import CountrySelectWidget
from django.forms.widgets import TimeInput
from phonenumber_field.formfields import PhoneNumberField
from webdata.custom_functions.helper_functions import geocode_address

############## GENERAL WEBPAGES FORMS ##############

# login form
class UserLoginForm(forms.Form):
    username = forms.CharField(max_length=100)  # define username field
    password = forms.CharField(widget=forms.PasswordInput(attrs={'id': 'password-field'}))  #password field

# registration forms
class UserRegistrationForm(UserCreationForm):
    class Meta:
        model = CustomUser
        fields = ['username', 'password1', 'password2']
        help_texts = {
            'username': 'Note: Once set, your username cannot be changed.',
        }

# customer registration form
class CustomerProfileForm(forms.ModelForm):
    phone_number = PhoneNumberField(region="SG")

    date_of_birth = forms.CharField(
        required=True,
        widget=forms.TextInput(attrs={'placeholder': 'YYYY-MM-DD'})
    )

    class Meta:
        model = CustomerInfo
        fields = ('first_name', 'middle_name', 'last_name', 'date_of_birth',
                'phone_number', 'email', 'address', 'country',
                'alert_radius', 'sms_alert', 'email_alert', 'long', 'lat')
        
        widgets = {
            'country': CountrySelectWidget(attrs={'class': 'form-control'}),
            'long': forms.HiddenInput(),  # hide the longitude field
            'lat': forms.HiddenInput(),   # hide the latitude field
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # remove error messages for hidden fields
        if 'long' in self.fields and 'long' in self.errors:
            del self.errors['long']

        if 'lat' in self.fields and 'lat' in self.errors:
            del self.errors['lat']

    def clean(self):
        # convert address to geospatial coordinates
        cleaned_data = super().clean()
        address = cleaned_data.get('address')
        country = cleaned_data.get('country')

        if address and country:
            try:
                full_address = address + country
                latitude, longitude = geocode_address(full_address)

                if longitude is None or latitude is None:
                    raise ValidationError("Unable to retrieve coordinates for the provided address. Please enter a valid or broader address.")
                
                # set the longitude and latitude in the cleaned data
                cleaned_data['long'] = longitude
                cleaned_data['lat'] = latitude

            except Exception as e:
                raise ValidationError(e)

        return cleaned_data

# business registration form
class BusinessProfileForm(forms.ModelForm):
    phone_number = PhoneNumberField(region="SG") # defaults to Singapore if country code not specified

    class Meta:
        model = BusinessInfo
        fields = ('business_name', 'description',
                  'phone_number', 'email', 'address', 'country',
                  'opening_time', 'closing_time', 'long', 'lat', 'business_image')
        
        widgets = {
            'country': CountrySelectWidget(attrs={'class': 'form-control'}),
            'long': forms.HiddenInput(),  # hide the longitude field
            'lat': forms.HiddenInput(),   # hide the latitude field
            'opening_time': TimeInput(attrs={'class': 'form-control', 'type': 'time'}),  # time input for opening time
            'closing_time': TimeInput(attrs={'class': 'form-control', 'type': 'time'}),  # time input for closing time
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # remove error messages for hidden fields
        if 'long' in self.fields and 'long' in self.errors:
            del self.errors['long']
        if 'lat' in self.fields and 'lat' in self.errors:
            del self.errors['lat']

    def clean(self):
        # convert address to geospatial coordinates
        cleaned_data = super().clean()
        address = cleaned_data.get('address')
        country = cleaned_data.get('country')

        if address and country:
            try:
                full_address = address + country
                latitude, longitude = geocode_address(full_address)

                if longitude is None or latitude is None:
                    raise ValidationError("Unable to retrieve coordinates for the provided address. Please enter a valid or broader address.")
                
                # set the longitude and latitude in the cleaned data
                cleaned_data['long'] = longitude
                cleaned_data['lat'] = latitude

            except Exception as e:
                raise ValidationError(e)

        return cleaned_data

############## FORMS FOR BOTH BUSINESSES AND CUSTOMERS ##############

# update password
class UpdatePassword(forms.Form):
    new_password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        label="New Password"
    )
    confirm_password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        label="Confirm Password"
    )

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("new_password")
        confirm_password = cleaned_data.get("confirm_password")

        if password and confirm_password and password != confirm_password:
            raise forms.ValidationError("Passwords do not match.")

        return cleaned_data

############## CUSTOMER-SPECIFIC FORMS ##############

# reservation form
class ReserveFoodItem(forms.Form):
    food_item = forms.ChoiceField(
        widget=forms.Select(attrs={'placeholder': 'Food Item'}),
        required=True,
        label="Food Item"
    )

    quantity = forms.TypedChoiceField(
        choices=[(1, 1), (2, 2)],
        coerce=int,
        required=True
    )

    def __init__(self, *args, **kwargs):
        # capture business_id from kwargs or request
        business_id = kwargs.pop('business_id', None)

        # initialise the parent class
        super().__init__(*args, **kwargs)

        if business_id:
            # retrieve food items for the given business/restaurant
            food_items = FoodLog.objects.filter(business_id=business_id, avail_status='available')
            choices = [(item.item_id, f"{item.quantity} {item.food_item} {item.units} for ${item.price_per_unit}") for item in food_items]
            # set the choices for the foodItem dropdown
            self.fields['food_item'].choices = choices

# search page form for filtering
class FilterFoodItem(forms.Form):
    min_distance = forms.DecimalField(
        widget=forms.NumberInput(attrs={'placeholder': 'Min Distance (0-10) - km', 'min': 0, 'max': 10}),
        required=False,
    )

    max_distance = forms.DecimalField(
        widget=forms.NumberInput(attrs={'placeholder': 'Max Distance (0-10) - km', 'min': 0, 'max': 10}),
        required=False,
    )

    min_cost = forms.DecimalField(
        widget=forms.NumberInput(attrs={'placeholder': 'Min Cost - $', 'min': 0}),
        required=False,
    )

    max_cost = forms.DecimalField(
        widget=forms.NumberInput(attrs={'placeholder': 'Max Cost - $', 'min': 0}),
        required=False,
    )

    item_name = forms.CharField(
        widget=forms.TextInput(attrs={'placeholder': 'Item Name'}),
        required=False,
    )

    restaurant_name = forms.CharField(
        widget=forms.TextInput(attrs={'placeholder': 'Establishment Name'}),
        required=False,
    )

    DIETARY_CHOICES = DietaryReg.DIETARY_CHOICES
    dietary_preferences = forms.MultipleChoiceField(
        choices=DIETARY_CHOICES,
        widget=forms.CheckboxSelectMultiple(),
        required=False
    )

############## BUSINESS-SPECIFIC FORMS ##############

# log a purchase via reservation ID
class BusinessLogPurchaseResID(forms.Form):
    reservationID = forms.IntegerField(
        widget=forms.NumberInput(attrs={'placeholder': 'Reservation ID'}),
        required=True,
        label="Reservation ID"
    )

# log a purchase manually using dropdown menu
class BusinessLogPurchaseManual(forms.Form):
    customerUsername = forms.CharField(
        widget=forms.TextInput(attrs={'placeholder': 'Customer Username'}),
        required=True,
        label="Customer Username"
    )

    offer = forms.ChoiceField(
        widget=forms.Select(attrs={'placeholder': 'Food Offer'}),
        required=True,
        label="Food Offer",
        choices=[]
    )

    quantity = forms.IntegerField(
        widget=forms.NumberInput(attrs={'placeholder': 'Quantity'}),
        required=True,
        label="Quantity",
        min_value = 1,
    )

    def __init__(self, *args, **kwargs):
        # dropdown will be in this format: 1 Pasta Sauce 200 ml Bottle for $4.00 [EXP: 2025-01-01]
        dropdown_options = kwargs.pop('dropdown_options', [])
        super().__init__(*args, **kwargs)
        self.fields['offer'].choices = dropdown_options

# dietary restrictions the business caters to
class DietaryCheckForm(forms.Form):
    DIETARY_CHOICES = [
        ('vegetarian', 'Vegetarian'),
        ('vegan', 'Vegan'),
        ('kosher', 'Kosher'),
        ('halal', 'Halal'),
        ('jain', 'Jain')
    ]

    dietary_preferences = forms.MultipleChoiceField(
        choices=DIETARY_CHOICES,
        widget=forms.CheckboxSelectMultiple(),
        required=False
    )
