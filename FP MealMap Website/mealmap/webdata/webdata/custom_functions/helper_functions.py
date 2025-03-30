import math, googlemaps, csv
from datetime import datetime, timedelta
from django.contrib import messages
from django.shortcuts import redirect
from ..credentials import GOOGLE_MAPS_API_KEY
from ..models import FoodLog

# connect to Google maps
gmaps = googlemaps.Client(key=GOOGLE_MAPS_API_KEY)

# converts address to geospatial coordinates (long & lat)
def geocode_address(address):
    try:
        geo_data = gmaps.geocode(address)
        if geo_data:
            location = geo_data[0]['geometry']['location']
            return location['lat'], location['lng']
        
        else:
            return None, None
        
    except Exception as e:
        print(f"Geocoding failed: {str(e)}")
        return None, None

# calculates distance between pairs of geospatial coordinates using Haversine formula
# and returns True/False and distance
def haversine(lat1, long1, lat2, long2, limit):

    # earth radius in kilometers
    R = 6371.0
    
    # convert latitude and longitude from degrees to radians
    lat1_rad, lon1_rad = math.radians(lat1), math.radians(long1)
    lat2_rad, lon2_rad = math.radians(lat2), math.radians(long2)
    
    # differences in coordinates
    dlat = lat2_rad - lat1_rad
    dlon = lon2_rad - lon1_rad
    
    # apply Haversine formula
    a = math.sin(dlat / 2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    
    # distance in kilometers
    distance = R * c

    # if distance within limit
    if distance < limit:
        return [True, distance]
    
    # if distance outside of limit
    else:
        return [False, distance]

# get all offers within 10km radius of the customer
def display_offers(customer_profile):
    foodItems = FoodLog.objects.select_related('business').filter(avail_status='available').order_by('-created_at').all()
    offers = []

    for food in foodItems:
        within_rad = haversine(customer_profile.lat, customer_profile.long, food.business.lat, food.business.long, 10)[0]
        if within_rad:
            offers.append(food)

    return offers

# get all offers within 10km radius of the customer after filtering
def display_offers_by_filter(customer_profile, min_distance=None, max_distance=None, min_cost=None, max_cost=None, item_name=None, restaurant_name=None, dietary_preferences=None):
    food_items = FoodLog.objects.filter(avail_status='available').order_by('-created_at').all()
    offers = []

    # filter based on the given parameters
    for food in food_items:
        within_rad = haversine(customer_profile.lat, customer_profile.long, food.business.lat, food.business.long, 10)[0]
        
        if within_rad:
            offers.append(food)
    
    if min_distance is not None:
        offers = [offer for offer in offers if haversine(customer_profile.lat, customer_profile.long, offer.business.lat, offer.business.long, 10)[1] >= min_distance]
    
    if max_distance is not None:
        offers = [offer for offer in offers if haversine(customer_profile.lat, customer_profile.long, offer.business.lat, offer.business.long, 10)[1] <= max_distance]
    
    if min_cost is not None:
        offers = [offer for offer in offers if offer.price_per_unit >= min_cost]
    
    if max_cost is not None:
        offers = [offer for offer in offers if offer.price_per_unit <= max_cost]
    
    if item_name is not None:
        offers = [offer for offer in offers if item_name.lower() in offer.food_item.lower()]

    if restaurant_name is not None:
        offers = [offer for offer in offers if restaurant_name.lower() in offer.business.business_name.lower()]

    if dietary_preferences is not None and dietary_preferences != []:
        offers = [offer for offer in offers
                  if any(diet in offer.business.dietary_preferences.all().values_list('dietary_opt', flat=True)
                         for diet in dietary_preferences)
                ]

    return offers

# ensure that the expiry date input for logging food items is > 24 hours from today
def validate_expiry_date(day, month, year, hour, minute, second):
    try:
        expiry_date = datetime(int(year), int(month), int(day), int(hour), int(minute), int(second))
        if expiry_date <= datetime.now() + timedelta(hours=24):
            return None, "Expiry date must be at least 24 hours in the future."
        return expiry_date, None
    
    except ValueError:
        return None, "Invalid expiry date format."

# validates data in CSV file
def check_csv(file, request):
    try:
        reader = csv.reader(file.read().decode('utf-8').splitlines()) # get CSV data
        errors = [] # stores all errors
        food_item_log = [] # stores logged items
        
        headers = next(reader, None)  # get the headers, or None if empty

        # checks CSV columns
        expected_headers1 = ['\ufeffitem_name', 'quantity_per_unit', 'unit', 'price_per_unit', 
                            'total_units', 'expiry_day', 'expiry_month', 'expiry_year', 
                            'expiry_hour', 'expiry_minute', 'expiry_second']
        
        expected_headers2 = ['item_name', 'quantity_per_unit', 'unit', 'price_per_unit', 'total_units', 'expiry_day', 'expiry_month', 'expiry_year', 'expiry_hour', 'expiry_minute', 'expiry_second']

        if headers != expected_headers1 and headers != expected_headers2:
            messages.error(request, 'Columns are incorrect. Ensure that the columns follow template_log.csv file columns.')
            return redirect('business-upload-log')

        check_count = 0 # checks total parsed rows in CSV file
        for row_num, row in enumerate(reader, start=2):  # start from line 2
            check_count += 1
            row_errors = []

            if len(row) != len(expected_headers1):
                row_errors.append(f"Row {row_num}: Incorrect number of columns.")
                continue  # skip processing this row

            item_name, quantity_per_unit, unit, price_per_unit, total_units, *expiry_values = row

            # check for empty values
            if not item_name.strip():
                row_errors.append(f"Row {row_num}: item_name column cannot be blank.")
            if not unit.strip():
                row_errors.append(f"Row {row_num}: unit column cannot be blank.")

            # convert to numeric values (integer and float)
            try:
                quantity_per_unit = int(quantity_per_unit)
                if quantity_per_unit <= 0:
                    row_errors.append(f"Row {row_num}: quantity_per_unit column must be at least 1.")
            except ValueError:
                row_errors.append(f"Row {row_num}: quantity_per_unit column must be an integer.")

            try:
                price_per_unit = float(price_per_unit)
                if price_per_unit < 0:
                    row_errors.append(f"Row {row_num}: price_per_unit column must be 0 or greater.")
            except ValueError:
                row_errors.append(f"Row {row_num}: price_per_unit column must be a valid number.")

            try:
                total_units = int(total_units)
                if total_units < 1:
                    row_errors.append(f"Row {row_num}: total_units column must be at least 1.")
            except ValueError:
                row_errors.append(f"Row {row_num}: total_units column must be an integer.")

            # validate expiry date
            expiry_date, expiry_error = validate_expiry_date(*expiry_values)
            if expiry_error:
                row_errors.append(f"Row {row_num}: {expiry_error}")

            # store row errors and skip processing if there are any
            if row_errors:
                errors.extend(row_errors)
                continue

            # if no errors, prepare the food log entry
            food_item_log.append({
                "item_name": item_name,
                "quantity_per_unit": quantity_per_unit,
                "unit": unit,
                "price_per_unit": price_per_unit,
                "total_units": total_units,
                "curr_quantity": total_units,  # Initialize with total units
                "expiry_date": str(expiry_date),
                "row": check_count
            })

        # if empty CSV file submitted
        if check_count == 0:
            messages.error(request, 'You are uploading an empty CSV file. Please check again.')
            return redirect('business-upload-log')

        # add errors to display
        if errors:
            messages.error(request, "Errors found in CSV file:")
            for error in errors:
                messages.error(request, error)
            return redirect('business-upload-log')
        
        request.session['food_log_upload_data'] = food_item_log
        return redirect('business-review-log')

    # throw error
    except Exception as e:
            messages.error(request, f'Error processing the CSV file: {str(e)}.')
            return redirect('business-upload-log')


