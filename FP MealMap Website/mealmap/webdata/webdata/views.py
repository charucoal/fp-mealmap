from django.contrib import messages
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.db import IntegrityError
from django.http import HttpResponse, HttpResponseForbidden
from django.db.models import Count, Q
from django.shortcuts import render, redirect
from webdata.custom_functions.helper_functions import *
from webdata.custom_functions.queue_data import *
from celery import chain
from .custom_functions import *
from .decorators import *
from .forms import *

# landing page, redirected to homepage 
def index(request):
    return redirect('home')

####################### LOGGED OUT PAGES #######################

@check_login
# renders homepage
def home(request):
    return render(request, 'webdata/g_homepage.html')

@check_login
# renders login page
def user_login(request):
    # if data submitted
    if request.method == 'POST':
        form = UserLoginForm(request.POST)

        # form is validated
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            # user is authenticated
            user = authenticate(request, username=username, password=password)

            # ensure user authentication was successful
            if user is not None:
                # logs user in and decorator handles redirection to correct homepage
                login(request, user)
                return redirect('home')

            # displays error message
            else:
                messages.error(request, 'Invalid username or password.')
    
    # displays empty form
    else:
        form = UserLoginForm()
    
    return render(request, "webdata/g_login.html", {'form': form})

# when logout is clicked, user is logged out
# and redirected to homepage
def user_logout(request):
    logout(request)
    return redirect('home')

@check_login
# renders registration page (for both customer and business)
def register(request, account_type):
    # intialise registration-related variables
    registered = False
    redirect_url = ''

    # intialise forms with POST data or display empty
    user_form = UserRegistrationForm(request.POST or None)
    # choose form to display according to the account type chosen
    profile_form = CustomerProfileForm(request.POST or None) if account_type == 'customer' else BusinessProfileForm(request.POST or None, files=request.FILES)
    
    if request.method == 'POST':
        # validate form data
        if user_form.is_valid() and profile_form.is_valid():
            # save the form data but don't commit to db yet
            user = user_form.save(commit=False)
            profile = profile_form.save(commit=False)

            profile.user = user
            profile.save() # save profile form to db

            user.account_type = account_type
            if account_type == 'customer':
                user.customer = profile
            else:
                user.business = profile

            user.save() # save user form to db

            registered = True # show success message
            redirect_url = 'login' # assign redirection url

        else:
            # iterate through and display all errors in the form
            for field, errors in profile_form.errors.items():
                for error in errors:
                    messages.error(request, error)

            for field, errors in user_form.errors.items():
                for error in errors:
                    messages.error(request, error)

    return render(request, "webdata/g_signup.html", {'account_type': 'Customer' if account_type == 'customer' else 'Business',
                                                    'user_form': user_form,
                                                    'profile_form': profile_form,
                                                    'registered': registered,
                                                    'redirect_url': redirect_url})

# view for customer registration
def register_customer(request):
    return register(request, account_type='customer')

# view for business registration
def register_business(request):
    return register(request, account_type='business')

####################### BUSINESS PAGES #######################

@business_required
# renders landing page for business accounts
def business_home(request):
    # retrieve logged in business profile
    business_profile = request.user.business
    # retrieve food items which are available
    food_items = FoodLog.objects.filter(business=business_profile, avail_status='available',
                                        expiry_date__gt=timezone.now()).order_by('-item_id').annotate(
                                            reservation_count=Count('reservations', filter=Q(reservations__res_status='open')))

    return render(request, 'webdata/b_homepage.html', {'business_profile': business_profile,
                                                       'items': food_items})

@business_required
def business_profile(request):
    # retrieve logged in business profile
    business_profile = request.user.business
    # get dietary options business caters to
    selected_preferences = list(DietaryReg.objects.filter(business=business_profile).values_list('dietary_opt', flat=True))

    # initialise form with business instance's details for display
    form = BusinessProfileForm(instance=business_profile)
    dietary_form = DietaryCheckForm(initial={'dietary_preferences': selected_preferences})

    # if form is updated
    if request.method == "POST":
        # check action type
        action_type = request.POST.get('action')

        # delete action
        if action_type == 'DELETE ACCOUNT':
            # get business instance, delete from db and logout
            business_info = BusinessInfo.objects.get(business_id=business_profile.business_id)
            business_info.delete()
            logout(request)

            return redirect('business-signup')
        
        # update dietary catering action
        elif action_type == 'Confirm Dietary Changes':
            # get updated details
            dietary_form = DietaryCheckForm(request.POST)
            if dietary_form.is_valid():
                # convert new dietary pref to set
                selected_preferences = set(dietary_form.cleaned_data['dietary_preferences'])
                # convert prev dietary pref to set
                existing_preferences = set(DietaryReg.objects.filter(business=business_profile).values_list('dietary_opt', flat=True))
                
                # identify unchecked options
                unchecked_options = existing_preferences - selected_preferences

                # identify newly checked options
                new_options = selected_preferences - existing_preferences

                # delete unchecked options
                DietaryReg.objects.filter(business=business_profile, dietary_opt__in=unchecked_options).delete()

                # create new instances of dietary instance 
                for option in new_options:
                    DietaryReg.objects.get_or_create(business=business_profile, dietary_opt=option)

                messages.success(request, 'Dietary catering options updated sucessfully.')

                return redirect('business-profile')
        
        # profile update action
        else:
            form = BusinessProfileForm(request.POST, files=request.FILES, instance=business_profile)
            # validate and save new data to db
            if form.is_valid():
                form.save()
                messages.success(request, 'Profile updated sucessfully!')

            else:
                for field, errors in form.errors.items():
                    for error in errors:
                        messages.error(request, error)

    return render(request, 'webdata/b_profilepage.html', {"form": form,
                                                          "dietary_form": dietary_form,
                                                          "business_profile": business_profile})

@business_required
def business_setpassword(request):
    # retrieve logged in business profile
    business_profile = request.user

    # if password is updated
    if request.method == "POST":
        # get form data
        form = UpdatePassword(request.POST)

        # validate data and save to db
        if form.is_valid():
            new_password = form.cleaned_data['new_password']
            business_profile.set_password(new_password)
            business_profile.save()

            update_session_auth_hash(request, business_profile)
            
            messages.success(request, "Password updated successfully!")
            return redirect('business-set-password')
        
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, error)

    else:
        # display empty form instance
        form = UpdatePassword()
        
    return render(request, 'webdata/b_passwordpage.html', {'form': form,
                                                           'username': business_profile})

@business_required
# renders all purchases made from the business
def business_view_purchases(request):
    # retrieve logged in business profile
    business_profile = request.user.business
    # filter purchases related to this business
    purchases = PurchaseLog.objects.filter(item__business=business_profile).order_by('-purchase_id')

    return render(request, 'webdata/b_purchasehistory.html', {'purchases': purchases})

@business_required
# renders entire food log history
def business_view_foodlog(request):
    # retrieve logged in business profile
    business_profile = request.user.business
    # filter for items logged by this business
    food_items = FoodLog.objects.filter(business=business_profile).order_by('-item_id')

    return render(request, 'webdata/b_foodlog.html', {'items': food_items})

@business_required
# renders reservation details page
def business_view_reservation(request):
    # retrieve logged in business profile
    business_profile = request.user.business
    # get reservations for items of this business
    res_items = ReservationLog.objects.filter(item__business=business_profile)

    # filter by res status
    open_res = res_items.filter(res_status='open').order_by('-res_id')
    collected_res = res_items.filter(res_status='collected').order_by('-res_id')
    expired_res = res_items.filter(res_status='expired').order_by('-res_id')

    all_res = [['Open Reservations', open_res],
               ['Collected Reservations', collected_res],
               ['Expired Reservations', expired_res]]

    return render(request, 'webdata/b_viewreservation.html', {'all_res': all_res})

@business_required
# RENDERS 2 FORMS (RES ID & MANUAL INPUT) FOR LOGGING PURCHASES
def business_log_purchase(request):
    # retrieve logged in business profile
    business_profile = request.user.business

    # get reservations and items associated to this business
    res_items = ReservationLog.objects.filter(item__business=business_profile)
    food_items = FoodLog.objects.filter(business=business_profile, avail_status = 'available')

    # add items to dropdown menu
    dropdown_options = [[item.item_id,
                         f"{item.quantity} {item.food_item} {item.units} for ${item.price_per_unit} [EXP: {item.expiry_date}]"]
                         for item in food_items]

    # intialise empty form or submitted data
    res_id_form = BusinessLogPurchaseResID(request.POST or None)
    manual_form = BusinessLogPurchaseManual(request.POST or None, dropdown_options=dropdown_options)
    
    error_for = None

    # if form is submitted
    if request.method == "POST":    
        # if res_id_form is submitted
        if res_id_form.is_valid():
            error_for = 'res_id'
            # get list of res ids submitted
            res_ids = request.POST.getlist('reservationID')

            # update reservation instances to collected
            to_update = []
            for res_id in res_ids:
                item = res_items.filter(res_id=int(res_id), res_status='open').first()
                if item:
                    item.res_status = 'collected'
                    item.collection_date_time = timezone.now()
                    to_update.append(item)
                
                # return error if res ID(s) are invalid
                else:
                    messages.error(request, 'Reservation ID(s) are invalid.')
                
            # if not update db with new data
            if to_update:
                res_items.model.objects.bulk_update(to_update, ['res_status', 'collection_date_time'])
                # redierct to reservation log page
                return redirect('businses-view-reservation')

        # if manual form is submitted
        if manual_form.is_valid():
            error_for = 'manual'

            # get form data
            customer_username = request.POST.get('customerUsername', None)
            offer_ids = request.POST.getlist('offer')
            quantities = request.POST.getlist('quantity')

            try:
                # get customer based on username
                user = CustomUser.objects.get(username=customer_username, customer_id__isnull=False)
            
                # check for repeated selections
                if len(offer_ids) > len(set(offer_ids)):
                    messages.error(request, 'There are repeated selections of food items.')

                else:
                    # fetch all food items at once
                    food_items_map = {food_item.item_id: food_item for food_item in food_items.filter(item_id__in=[int(offer_id) for offer_id in offer_ids], avail_status='available')}

                    to_update = []
                    update_purchase_log = []
                    
                    for offer_id, quantity in zip(offer_ids, quantities):
                        # get food item
                        food_item = food_items_map.get(int(offer_id))

                        # if food item instance does not exist, throw an error
                        if not food_item:
                            messages.error(request, 'One or more items are unavailable.')
                            break
                        
                        # if quantity chosen is more than present quantity, throw an error
                        if food_item.curr_quantity < int(quantity):
                            messages.error(request, f'Quantity of "{food_item.food_item}" selected exceeds quantity left.')
                            break
                        
                        # create new instance of purchase
                        purchase_log = PurchaseLog(
                            customer_id=user.customer_id,
                            item_id=offer_id,
                            quantity=quantity,
                        )

                        # add to list of updates
                        update_purchase_log.append(purchase_log)

                        # update quantity
                        food_item.curr_quantity -= int(quantity)
                        # if quantity == 0, set to unavailable
                        if food_item.curr_quantity == 0:
                            food_item.avail_status = 'unavailable'

                        # add to list of updates
                        to_update.append(food_item)

                        # perform updates
                        if to_update:
                            FoodLog.objects.bulk_update(to_update, ['curr_quantity', 'avail_status'])

                        if update_purchase_log:
                            PurchaseLog.objects.bulk_create(update_purchase_log)

                        # redirect to purchase history page
                        return redirect('business-view-purchase')
            
            except CustomUser.DoesNotExist:
                # throw an error if customer not found
                messages.error(request, 'Customer not found.')

    return render(request, 'webdata/b_logpurchase.html', {'res_id_form': res_id_form,
                                                          'manual_form': manual_form,
                                                          'error_for': error_for})

@business_required
# renders 2 forms (within the HTML) to upload new food items via
def business_upload_foodlog(request):
    request.session['allowed_to_access_check'] = True

    # retrieve logged in business profile
    business_profile = request.user.business

    # check closing time
    today_closing_time = datetime.combine(timezone.now().date(), business_profile.closing_time)

    # if it is after closing time, page is not accessible
    if timezone.now() > today_closing_time:
        return HttpResponseForbidden('Your establishment is currently closed, alerts cannot be sent at this time.')

    # if it is 1 hour to closing time, page is also not accessible
    elif timezone.now() + timedelta(hours=1) > today_closing_time:
        return HttpResponseForbidden('Your establishment is closing soon, alerts cannot be sent at this time.')

    return render(request, 'webdata/b_alertpage.html')

@business_required
# logic to check data uploaded via CSV file
# and redirect to review page
def business_upload_foodlog_csv(request):
    # review page is only accessible if request.session is given
    if not request.session.pop('allowed_to_access_check', False):
        return HttpResponseForbidden("You cannot access this page directly.")

    if request.method == 'POST':
        # file is checked for validity
        file = request.FILES.get("csv_file")

        if not file:
            messages.error(request, 'No file was uploaded.')
            return redirect('business-upload-log')

        else:
            request.session['allowed_to_access_review'] = True
            # check_csv redirects back to upload log page if error
            # and redirects to review page if no errors
            return check_csv(file, request)
    
    return HttpResponseForbidden("You cannot access this page directly.")

@business_required
# logic to process form data
# and redirect to review page
def business_upload_foodlog_manual(request):
    # review page is only accessible if request.session is given
    if not request.session.pop('allowed_to_access_check', False):
        return HttpResponseForbidden("You cannot access this page directly.")

    if request.method == 'POST':
        # get form data
        food_item_log = []
        total_items = len(request.POST.getlist('food_item'))

        for i in range(total_items):
            food_item_log.append({"item_name": request.POST.getlist('food_item')[i],
                                  "quantity_per_unit": request.POST.getlist('quantity')[i],
                                  "unit": request.POST.getlist('units')[i],
                                  "price_per_unit": request.POST.getlist('price_per_unit')[i],
                                  "total_units": request.POST.getlist('total_units')[i],
                                  "curr_quantity": request.POST.getlist('total_units')[i],
                                  "expiry_date": request.POST.getlist('expiry_date')[i],
                                  "row": i+1})

        request.session['food_log_upload_data'] = food_item_log
        request.session['allowed_to_access_review'] = True
        # redirect to review page
        return redirect('business-review-log')

    return HttpResponseForbidden("You cannot access this page directly.")

@business_required
# renders review log page
def business_review_foodlog(request):
    if request.method == 'GET':
        # review page is only accessible if request.session is given
        if not request.session.pop('allowed_to_access_review', False):
            return HttpResponseForbidden("You cannot access this page directly.")
        
        else:
            # displays the newly logged items for review
            request.session['allowed_to_upload'] = True
            food_log_upload_data = request.session.get('food_log_upload_data')
            return render(request, 'webdata/b_reviewlogpage.html', {'food_log_upload_data': food_log_upload_data})

    if request.method == 'POST':
        # review page is only accessible if request.session is given
        if not request.session.pop('allowed_to_upload', False):
            return HttpResponseForbidden("You cannot access this page directly.")
        
        else:
            # items saved into database when "Send out Alerts!" is clicked
            food_log_upload_data = request.session.get('food_log_upload_data')
            business_profile = request.user.business
            update_food_log = []

            for item in food_log_upload_data:
                update_food_log.append(FoodLog(business=business_profile,
                                               food_item=item['item_name'],
                                               quantity=item['quantity_per_unit'],
                                               units=item['unit'],
                                               price_per_unit=item['price_per_unit'],
                                               total_units=item['total_units'],
                                               curr_quantity=item['total_units'],
                                               expiry_date=item['expiry_date']))

            FoodLog.objects.bulk_create(update_food_log)
            item_ids = [food_log.item_id for food_log in update_food_log]
            request.session['item_ids_log'] = item_ids

            # redirected to view to send out alerts
            return redirect('business-alert-log')

    return HttpResponseForbidden("You cannot access this page directly.")

# logic to send out alerts
def send_out_alerts(request):
    # retrieve logged in business profile 
    business_profile = request.user.business
    # get newly logged items' IDs from request.session
    log_data = request.session.get('item_ids_log')

    # get customer profiles
    customers = CustomerInfo.objects.all()

    # filter customers by distance band
    customers_within_3km, customers_within_5km, customers_within_10km = get_relevant_customers_for_alert(customers, business_profile)
    print(len(customers_within_3km), len(customers_within_5km), len(customers_within_10km)) # print for logging

    ##################### ASYNC COMMENTED OUT FOR NOW, UNCOMMENT WHEN NEEDED #####################

    # # convert to json format for processing in Celery
    # customers_within_3km_json = convert_to_json(customers_within_3km)
    # customers_within_5km_json = convert_to_json(customers_within_5km)
    # customers_within_10km_json = convert_to_json(customers_within_10km)

    # business = model_to_json(business_profile)

    # json_data = [model_to_json(FoodLog.objects.get(item_id=item_id)) for item_id in log_data]

    # statements = create_alert_statement(json_data, business) # create info statement to send out

    # # immediately queue to send out alerts to customers in the 0-3km band
    # queue_alerts.delay(statements, customers_within_3km_json)

    # # queue alerts to be sent after 60s for customers in 3-5km band
    # chain(
    #     get_latest_quantity.s(log_data, business),  # Task 1: Get latest quantity after 59s
    #     queue_alerts.s(customers_within_5km_json)  # Task 2: Send alert after fetching latest data
    # ).apply_async(countdown=2)  # Runs at 60s

    # # queue alerts to be sent after 120s for customers in 5-10km band
    # chain(
    #     get_latest_quantity.s(log_data, business),  # Task 1: Get latest quantity after 119s
    #     queue_alerts.s(customers_within_10km_json)  # Task 2: Send alert after fetching latest data
    # ).apply_async(countdown=120)  # Runs at 120s

    ##################### ASYNC COMMENTED OUT FOR NOW, UNCOMMENT WHEN NEEDED #####################

    # get total customers alert is sent to
    total_customers = len(customers_within_3km) + len(customers_within_5km) + len(customers_within_10km)
    messages.success(request, f"Customers queued to be alerted!\nApprox. {total_customers} customers will be alerted over the next hour.")

    # redirect to home which shows the newly logged items open for purchase
    return redirect('business-home')

####################### CUSTOMER PAGES #######################

@customer_required
# renders homepage with map and top 6 newest offers
def customer_home(request):
    # retrieve currently logged in customer
    customer_profile = request.user.customer

    # get all restaurants with available offers for customer
    offers = display_offers(customer_profile)
    restaurants = set(offer.business for offer in offers)

    # get top 6 newest offers
    top_six_offers = offers[:6]
    print(top_six_offers)

    return render(request, 'webdata/c_homepage.html', {'customer_profile': customer_profile,
                                                       'restaurants': restaurants,
                                                       'offers': top_six_offers})

@customer_required
# renders customer profile settings page
def customer_profile(request):
    # retrieve currently logged in customer
    customer_profile = request.user.customer

    # initialise empty form or with data
    form = CustomerProfileForm(request.POST or None, instance=customer_profile)

    # if form is submitted
    if request.method == "POST":
        action_type = request.POST.get('action')

        # if delete account is requested
        if action_type == 'DELETE ACCOUNT':
            # get and delete customer from db
            customer_info = CustomerInfo.objects.get(customer_id=customer_profile.customer_id)
            customer_info.delete()
            # log user out
            logout(request)

            # redirect to customer signup page
            return redirect('customer-signup')

        # if form is valid, save changes to db
        if form.is_valid():
            messages.success(request, 'Profile updated successfully!')
            form.save()

        # display errors if form is invalid
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, error)
    
    return render(request, 'webdata/c_profilepage.html', {'form': form})

@customer_required
# renders password reset page
def customer_setpassword(request):
    # retrieve currently logged in customer
    customer_profile = request.user
    
    # update password
    if request.method == "POST":
        # get form data
        form = UpdatePassword(request.POST)

        # if form is valid, save changes to db
        if form.is_valid():
            new_password = form.cleaned_data['new_password']
            customer_profile.set_password(new_password)
            customer_profile.save()

            update_session_auth_hash(request, customer_profile)
            
            messages.success(request, "Password updated successfully!")
            return redirect('customer-set-password')
        
        # display errors if form is invalid
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, error)

    else:
        # initialise new instance of form
        form = UpdatePassword()
        
    return render(request, 'webdata/c_passwordpage.html', {'form': form,
                                                           'username': customer_profile})

@customer_required
# renders purchase and reservation history page
def customer_purchase(request):
    # retrieve currently logged in customer
    customer_profile = request.user.customer

    # get items reserved by this customer
    res_items = ReservationLog.objects.filter(customer=customer_profile).order_by('-reservation_date_time')
    # get items purchased by this customer
    purchase_items = PurchaseLog.objects.filter(customer=customer_profile).order_by('-date_purchased')

    return render(request, 'webdata/c_purchase.html', {'purchase_detail': purchase_items,
                                                        'reservation_detail': res_items})

@customer_required
# renders open reservation details
def customer_view_reservation(request):
    # retrieve currently logged in customer
    customer_profile = request.user.customer
    
    # get items reserved by this customer which have a status of 'open'
    reservation_detail = ReservationLog.objects.filter(customer=customer_profile, res_status='open').order_by('-reservation_date_time')

    return render(request, 'webdata/c_reservepage.html', {'reservation_detail': reservation_detail})

@customer_required
# render restaurant details
def customer_view_restaurant(request):
    if request.method == "GET":
        # get business id
        business_id = request.GET.get('business_id')
        
        if not business_id:
            return redirect('customer_deals')
        
        # retrieve business profile and its offers
        try:
            business = BusinessInfo.objects.get(business_id=business_id)
            offers = FoodLog.objects.filter(business_id=business_id, avail_status='available')
        
        # show error if business does not exist
        except BusinessInfo.DoesNotExist:
            return HttpResponse(f"Business with the id '{business_id}' was not found.", status=404)

        return render(request, 'webdata/c_viewrestaurant.html', {'business_details': business,
                                                                 'offers': offers})

@customer_required
# renders reservation form to reserve offers from a business
def customer_make_reservation(request):
    # retrieve logged in customer profile
    user = request.user.customer

    # get business id
    business_id = request.GET.get('business_id')
    if not business_id:
        return redirect('customer_deals')
            
    try:
        # get business profile
        business = BusinessInfo.objects.get(business_id=business_id)

        # ensure customer is within distance band
        within_rad = haversine(user.lat, user.long, business.lat, business.long, 10)[0]
        if not within_rad:
            return HttpResponseForbidden(f"Unfortunately, this establishment is outside of the specified radius from your location, so we're unable to process a reservation at this time.")
        
        # ensure that reservation is placed during business hours
        if timezone.now().time() > business.closing_time or timezone.now().time() < business.opening_time:
            return HttpResponseForbidden(f"This establishment is currently closed, place a reservation at a later time.")
        
        # intialise empty form or with data
        form = ReserveFoodItem(request.POST or None, business_id=business_id)
        if request.method == "GET":
            return render(request, 'webdata/c_reserveform.html', {'form': form, 'business': business})

        # check if form is valid
        if request.method == "POST" and form.is_valid():
            # get form data
            item_ids = request.POST.getlist('food_item')
            c_quantities = request.POST.getlist('quantity')
            res_items_update = []
            food_quantity_update = []

            for item_id, c_quantity in zip(item_ids, c_quantities):
                try:
                    # get items requested for reservation
                    food_item = FoodLog.objects.get(item_id=item_id)
                    c_quantity = int(c_quantity)

                    # check if there is sufficient quantity
                    if food_item.curr_quantity < c_quantity:
                        messages.error(request, 'Not enough stock available for this reservation.')
                        break

                    else:
                        # create reservation instance
                        collection_date_time = timezone.now() + timedelta(minutes=20)
                        reservation = ReservationLog(customer=user,
                                                    item=food_item,
                                                    quantity=c_quantity,
                                                    collection_date_time=collection_date_time)
                        
                        res_items_update.append(reservation)

                        # update food item instance
                        food_item.curr_quantity -= c_quantity
                        food_quantity_update.append(food_item)

                # show error if item does not exist anymore
                except FoodLog.DoesNotExist:
                    messages.error(request, 'The selected food item does not exist.')
                
            try:
                # update changes to db
                if res_items_update and food_quantity_update :
                    ReservationLog.objects.bulk_create(res_items_update)
                    FoodLog.objects.bulk_update(food_quantity_update, ['curr_quantity'])
                    
                    # redirect to view reservations page if reservation successfully placed
                    return redirect('customer-view-reservation')
            
            # ensure that item(s) have not already been reserved by customer
            except IntegrityError:
                messages.error(request, 'You have already reserved one of the items. Ensure the items selected have not been initially reserved by you.')

        return render(request, 'webdata/c_reserveform.html', {'form': form, 'business': business})
    
    except BusinessInfo.DoesNotExist:
            return HttpResponse(f"Business with the id '{business_id}' was not found.", status=404)

@customer_required
# renders search bar and all offers available to customer
def customer_view_offers(request):
    # retrieve currently logged in customer
    customer_profile = request.user.customer

    # get all offers
    all_offers = display_offers_by_filter(customer_profile)

    # initialise form with filter data
    form = FilterFoodItem(request.GET)

    # filter data by parameter
    if request.method == "GET" and form.is_valid():
        min_distance = form.cleaned_data.get('min_distance')
        max_distance = form.cleaned_data.get('max_distance')
        min_cost = form.cleaned_data.get('min_cost')
        max_cost = form.cleaned_data.get('max_cost')
        item_name = form.cleaned_data.get('item_name')
        restaurant_name = form.cleaned_data.get('restaurant_name')
        dietary_preferences = form.cleaned_data.get('dietary_preferences')

        # returns food offers filtered based on parameters
        all_offers = display_offers_by_filter(customer_profile, min_distance, max_distance,
                                           min_cost, max_cost, item_name, restaurant_name,
                                           dietary_preferences)

    return render(request, 'webdata/c_dealspage.html', {'customer_profile': customer_profile,
                                                        'offers': all_offers,
                                                        'form': form})