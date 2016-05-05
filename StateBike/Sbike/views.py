from django.shortcuts import render
from django.shortcuts import redirect

from django.contrib import messages
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.hashers import make_password
from django.core.exceptions import ObjectDoesNotExist
from django.core.urlresolvers import reverse
from django.db import IntegrityError

from .forms import ClientRegisterForm, ClientEditPhoneForm, ClientEditEmailForm
from .forms import ClientEditNameForm, ClientEditPasswordForm
from .forms import ClientEditCardDataForm, CreateStationForm, RegisterForm

from itertools import chain

from .models import Client
from .models import Admin
from .models import Employee
from .models import Station
from .models import Bike
from .models import Loan
from .models import Sanction
from .models import Notification

from random import randint  # para las estaciones


# ##-----------------------------------------------------------------------## #
# ##----------------------------REGISTER-----------------------------------## #
# ##-----------------------------------------------------------------------## #
def clientRegisterView(request):
    if request.user.is_authenticated():
        return redirect('/webprofile')

    if request.method == 'POST':
        form = ClientRegisterForm(request.POST)

        if form.is_valid():
            cleaned_data = form.cleaned_data
            username = cleaned_data.get('username')
            password = cleaned_data.get('password1')
            first_name = cleaned_data.get('first_name')
            last_name = cleaned_data.get('last_name')
            email = cleaned_data.get('email')
            phone_number = cleaned_data.get('phone_number')
            dni = cleaned_data.get('dni')
            card_number = cleaned_data.get('card_number')
            expiration_date = cleaned_data.get('expiration_date')
            security_code = cleaned_data.get('security_code')

            user = User.objects.create_user(username, email, password)

            user.first_name = first_name
            user.last_name = last_name

            user.save()

            client = Client()
            client.user = user
            client.phone_number = phone_number
            client.dni = dni

            client.edit_card(card_number, expiration_date, security_code)

            messages.success(request, 'You Have Successfully Registered')
            return redirect('/weblogin')

    else:
        form = ClientRegisterForm()
    context = {
        'form': form
    }
    return render(request, 'Sbike/client_register.html', context)
# ##-----------------------------------------------------------------------## #
# ##----------------------------END--REGISTER------------------------------## #
# ##-----------------------------------------------------------------------## #


# ##-----------------------------------------------------------------------## #
# ##-------------------------------LOCATOR---------------------------------## #
# ##-----------------------------------------------------------------------## #
@login_required
def locatorView(request):
    stations = Station.objects.all()
    return render(request, 'Sbike/stations.html', {'stations': stations})

# ##-----------------------------------------------------------------------## #
# ##----------------------------END--LOCATOR-------------------------------## #
# ##-----------------------------------------------------------------------## #

# ##-----------------------------------------------------------------------## #
# ##--------------------------------HOME-----------------------------------## #
# ##-----------------------------------------------------------------------## #


def home(request):
    logout(request)
    return render(request, 'Sbike/home.html')

# ##-----------------------------------------------------------------------## #
# ##-----------------------------END--HOME---------------------------------## #
# ##-----------------------------------------------------------------------## #


# ##-----------------------------------------------------------------------## #
# ##----------------------------WEB--LOGIN---------------------------------## #
# ##-----------------------------------------------------------------------## #

def webLoginView(request):
    if request.user.is_authenticated():
        return redirect('/webprofile')

    message = ''
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(username=username, password=password)

        sanction = Sanction.objects.filter(client__user=user).first()

        if sanction is not None:
            is_over = sanction.is_over()
        else:
            is_over = None

        # si no hay sancion o la sancion es menor y ya pasaron los 5 dias
        if sanction is None or (sanction.is_minor and is_over):

            # si ya pasaron 5 dias, borrar la sancion
            if is_over:
                sanction.delete()

            if user is not None:
                if user.is_active:
                    login(request, user)
                    request.session['type'] = 'web'
                    employee = Employee.objects.filter(user=user)
                    if Admin.objects.filter(user=user).first() is not None:
                        request.session['user_type'] = 'admin'
                    elif employee.first() is not None:
                        request.session['user_type'] = 'employee'
                    else:
                        request.session['user_type'] = 'client'
                    return redirect('/webprofile')
                else:
                    message = 'Inactive User'
                    return render(request, 'login.html', {'message': message})
            message = 'Invalid username/password'

        else:
            messages.error(request, 'Sorry! You have a Active Sanction')
            return redirect('/home')

    return render(request, 'Sbike/web_login.html', {'message': message})

# ##-----------------------------------------------------------------------## #
# ##----------------------------WEB--LOGIN---------------------------------## #
# ##-----------------------------------------------------------------------## #


# ##-----------------------------------------------------------------------## #
# ##--------------------------STATION--LOGIN-------------------------------## #
# ##-----------------------------------------------------------------------## #

def get_random_station():
    # asignar una estacion random
    stations = Station.objects.all()
    chosen = randint(0, len(stations) - 1)

    # seleccionar la estacion i-esima
    i = 0
    for st in stations:
        if i == chosen:
            break
        i = i + 1
    return st.id


def stationLoginView(request):
    if request.user.is_authenticated() and ('station' in request.session):
        return redirect('/stationprofile')

    message = ''
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(username=username, password=password)

        sanction = Sanction.objects.filter(client__user=user).first()

        if sanction is not None:
            is_over = sanction.is_over()
        else:
            is_over = None

        # si no hay sancion o la sancion es menor y ya pasaron los 5 dias
        if sanction is None or (sanction.is_minor and is_over):

            # si ya pasaron 5 dias, borrar la sancion
            if is_over:
                sanction.delete()

            if user is not None:
                if user.is_active:
                    try:
                        request.session['station'] = get_random_station()
                    except ValueError:
                        return render(
                            request, 'Sbike/station_login.html',
                            {'message': 'There is no existing station'})

                    login(request, user)
                    request.session['type'] = 'station'
                    return redirect('/stationprofile')
                else:
                    return render(
                        request, 'Sbike/station_login.html',
                        {'message': 'Inactive User'})
            message = 'Invalid username/password'

        else:
            messages.error(request, 'Sorry! You have a Active Sanction')
            return redirect('/home')

    return render(request, 'Sbike/station_login.html', {'message': message})


# ##-----------------------------------------------------------------------## #
# ##------------------------END--STATION--LOGIN----------------------------## #
# ##-----------------------------------------------------------------------## #


# ##-----------------------------------------------------------------------## #
# ##------------------------------LOGOUT-----------------------------------## #
# ##-----------------------------------------------------------------------## #

@login_required
def logoutView(request):

    messages.success(request, 'You Have Successfully Logged Out!')
    s_type = request.session['type']
    logout(request)
    if (s_type == 'station'):
        return redirect('/stationlogin')
    return redirect('/weblogin')
# ##-----------------------------------------------------------------------## #
# ##-----------------------------END--LOGOUT-------------------------------## #
# ##-----------------------------------------------------------------------## #

# ##-----------------------------------------------------------------------## #
# ##---------------------------STATION-PROFILE-----------------------------## #
# ##-----------------------------------------------------------------------## #


@login_required
def stationProfile(request):
    if request.session['type'] == 'web':
        return redirect('/webprofile')
    username = request.user.get_username()
    clients = Client.objects.filter(user__username=username)

    if len(clients) == 1:
        # create basic info dict
        dict = createUserDict(clients[0])

        # add extra client info
        dict['card_number'] = clients[0].card_number
        dict['exp_date'] = clients[0].expiration_date
        dict['sec_code'] = clients[0].security_code

        return render(request, 'Sbike/station_profile.html', dict)

    else:
        logout(request)
        messages.error(request, 'Admin/Employee can not login!')
        return redirect('/stationlogin')

# ##-----------------------------------------------------------------------## #
# ##-----------------------END--STATION-PROFILE----------------------------## #
# ##-----------------------------------------------------------------------## #


# ##-----------------------------------------------------------------------## #
# ##---------------------------WEB-PROFILE---------------------------------## #
# ##-----------------------------------------------------------------------## #

@login_required
def webProfile(request):

        username = request.user.get_username()
        clients = Client.objects.filter(user__username=username)
        admins = Admin.objects.filter(user__username=username)
        employees = Employee.objects.filter(user__username=username)

        if len(clients) == 1:
            return clientProfile(request, clients[0])

        elif len(admins) == 1:
                return adminProfile(request, admins[0])

        elif len(employees) == 1:
            return employeeProfile(request, employees[0])

# Esto que sigue ya no deberia volver a ocurrir.
# Si alguien lo detecta. Avise!!
        else:
            messages.error(request, 'Error: Access Denied')
            return redirect('/home')
# ##-----------------------------------------------------------------------## #
# ##------------------------END--WEB--PROFILE------------------------------## #
# ##-----------------------------------------------------------------------## #


# ##-----------------------------------------------------------------------## #
# ##-------------------------PROFILE--FUNCTS-------------------------------## #
# ##-----------------------------------------------------------------------## #


def clientProfile(request, client, readOnly=False):

    # create basic info dict
    dict = createUserDict(client)

    # add extra client info
    dict['card_number'] = client.card_number
    dict['exp_date'] = client.expiration_date
    dict['sec_code'] = client.security_code

    dict['read_only'] = readOnly

    return render(request, 'Sbike/client_profile.html', dict)


def adminProfile(request, admin):

    dict = createUserDict(admin)

    # add notifications into dict
    dict['notif'] = Notification.objects.all()
    return render(request, 'Sbike/admin_profile.html', dict)


def employeeProfile(request, employee):

    dict = createUserDict(employee)
    return render(request, 'Sbike/employee_profile.html', dict)


def createUserDict(sbuser):

    dict = {}
    dict['fname'] = sbuser.user.first_name
    dict['lname'] = sbuser.user.last_name
    dict['username'] = sbuser.user.username
    dict['email'] = sbuser.user.email
    dict['dni'] = sbuser.dni
    dict['phone'] = sbuser.phone_number

    return dict

# ##-----------------------------------------------------------------------## #
# ##-------------------------PROFILE--FUNCTS-------------------------------## #
# ##-----------------------------------------------------------------------## #


# ##-----------------------------------------------------------------------## #
# ##-----------------------------LOANS-------------------------------------## #
# ##-----------------------------------------------------------------------## #


@login_required
def bikeLoan(request):
    if request.method == 'POST':

        client = Client.objects.get(user=request.user)
        try:
            bike_id = request.POST.get('select')
            bike = Bike.objects.get(id=bike_id)
            station = Station.objects.get(id=bike.station.id)
            loan = Loan()
            loan.create_loan(client, bike)

            # update data base after possible exception
            Bike.objects.filter(id=bike_id).update(state='TK')
            if station.stock() == 0:
                notif = Notification()
                notif.add_station(station)

            messages.success(request, 'Loan: Bike '+str(bike_id))
        except IntegrityError:
            messages.error(request, 'Sorry, You Have An Outstanding Loan')
        finally:
            return redirect('/stationprofile')
    try:
        bikes = Bike.objects.filter(state='AV',
                                    station_id=request.session['station'])
    except KeyError:
        messages.error(request, 'You Must Be Logged From A Station!')
        return redirect('/webprofile')

    if len(bikes) == 0:
        messages.error(request, 'Sorry, No Bikes Available!')
    return render(request, 'Sbike/bike_loan.html', ({'bikes': bikes}))

# ##-----------------------------------------------------------------------## #
# ##----------------------------END--LOANS---------------------------------## #
# ##-----------------------------------------------------------------------## #


# ##-----------------------------------------------------------------------## #
# ##----------------------------GIVE--BACK---------------------------------## #
# ##-----------------------------------------------------------------------## #
class SanctionExist(Exception):
    pass


@login_required
def givebackView(request):

    try:
        station = Station.objects.get(id=request.session['station'])
        # check if there is capacity available
        if station.total_stock() + 1 > station.capacity:
            messages.error(
                request, 'Sorry! There Is No Capacity In The Station!')
            return render(request, 'Sbike/give_back.html')
        client = Client.objects.get(user=request.user)
        try:
            # check if a sanction exists
            if (Sanction.objects.filter(client=client).first()) is not None:
                raise SanctionExist

            loan = Loan.objects.get(client=client)
            bike = Bike.objects.get(id=loan.bike.id)

        except SanctionExist:
            messages.error(request, 'Sorry! A Sanction is Pending')
            return render(request, 'Sbike/give_back.html')
        except ObjectDoesNotExist:
            messages.error(request, 'Sorry! No Loans Outstanding!!')
            return render(request, 'Sbike/give_back.html')

        if request.method == 'POST':
            bike_id = request.POST.get('select')

            loan = Loan.objects.get(bike=bike_id)
            loan.set_end_date()
            days = loan.eval_sanction()

            if days > 0:
                sanction = Sanction()
                sanction.create_sanction(loan, days)
            else:
                Loan.objects.filter(bike=bike_id).delete()

            # actualizar info de la bicicleta
            bike = Bike.objects.get(id=bike_id)
            bike.give_back()
            bike.move(station)

            message = 'Thanks For Return!'
            return render(
                request, 'Sbike/give_back.html', {'message': message})

        return render(request, 'Sbike/give_back.html', {'bike': bike})

    except KeyError:
        messages.error(request, 'You Must Be Logged From A Station!')
        return redirect('/webprofile')


# ##-----------------------------------------------------------------------## #
# ##------------------------END--GIVE--BACK--------------------------------## #
# ##-----------------------------------------------------------------------## #


# ##-----------------------------------------------------------------------## #
# ##------------------------EDIT---PASSWORD--------------------------------## #
# ##-----------------------------------------------------------------------## #


@login_required
def clientEditPassword(request):
    client = Client.objects.get(user=request.user)
    if request.method == 'POST':
        form = ClientEditPasswordForm(request.POST)

        if form.is_valid():
            cleaned_data = form.cleaned_data
            """comprueba cada campo que no este vacio"""
            """si no lo esta entonces modifica la base"""

            password = make_password(cleaned_data['password1'])
            if password:
                client.user.password = password
                messages.success(request, 'Password Changed Successfully')
            else:
                messages.error(request, 'Error! Password Null!')
            client.user.save()
            return redirect('/webprofile')

    form = ClientEditPasswordForm()
    context = {
        'form': form
    }
    return render(request, 'Sbike/client_edit.html', context)


# ##-----------------------------------------------------------------------## #
# ##----------------------------END--EDIT--PASSWORD------------------------## #
# ##-----------------------------------------------------------------------## #


# ##-----------------------------------------------------------------------## #
# ##--------------------------EDIT--CLIENT--CARD--DATA----- ---------------## #
# ##-----------------------------------------------------------------------## #


@login_required
def clientEditCardData(request):

    client = Client.objects.get(user=request.user)
    if request.method == 'POST':
        form = ClientEditCardDataForm(request.POST)
        if form.is_valid():
            cleaned_data = form.cleaned_data
            """comprueba cada campo que no este vacio"""
            """si no lo esta entonces modifica la base"""
            card_number = cleaned_data['card_number']
            expiration_date = cleaned_data['expiration_date']
            security_code = cleaned_data['security_code']

            client.edit_card(card_number, expiration_date, security_code)

            messages.success(request, 'Successfully Update!')
            return redirect('/editprofile/card')
    form = ClientEditCardDataForm()
    context = {
        'form': form
    }
    return render(request, 'Sbike/client_edit.html', context)

# ##-----------------------------------------------------------------------## #
# ##-------------------END--EDIT--CLIENT--CARD--DATA-----------------------## #
# ##-----------------------------------------------------------------------## #


# ##-----------------------------------------------------------------------## #
# ##----------------------EDIT--CLIENT--PHONE------------------------------## #
# ##-----------------------------------------------------------------------## #
@login_required
def ClientEditPhone(request):
    client = Client.objects.get(user=request.user)

    if request.method == 'POST':
        form = ClientEditPhoneForm(request.POST)
        if form.is_valid():
            cleaned_data = form.cleaned_data
            phone_number = cleaned_data['phone_number']
            client.edit_phone(phone_number)
            messages.success(
                request, 'Successfully Update! Phone: ' + str(phone_number))
            return redirect('/editprofile/phone')

    form = ClientEditPhoneForm()
    context = {
        'form': form
    }
    return render(request, 'Sbike/client_edit.html', context)


# ##-----------------------------------------------------------------------## #
# ##----------------------END--EDIT--CLIENT--PHONE-------------------------## #
# ##-----------------------------------------------------------------------## #

# ##-----------------------------------------------------------------------## #
# ##------------------------EDIT--CLIENT--EMAIL----------------------------## #
# ##-----------------------------------------------------------------------## #


@login_required
def ClientEditEmail(request):
    client = Client.objects.get(user=request.user)

    if request.method == 'POST':
        form = ClientEditEmailForm(request.POST)
        if form.is_valid():
            email = form.clean_email()
            client.edit_email(email)
            messages.success(
                request, 'Successfully Update! Email: ' + str(email))
            return redirect('/editprofile/email')

    form = ClientEditEmailForm()
    context = {
        'form': form
    }
    return render(request, 'Sbike/client_edit.html', context)


# ##-----------------------------------------------------------------------## #
# ##----------------------END--EDIT--CLIENT--EMAIL-------------------------## #
# ##-----------------------------------------------------------------------## #


# ##-----------------------------------------------------------------------## #
# ##--------------------------SET-BIKE-STATUS------------------------------## #
# ##-----------------------------------------------------------------------## #

@login_required
def setBikeStatus(request):
    try:
        # ver si es realmente un empleado
        SMaster = Employee.objects.get(user=request.user)
        # obtener todas las estaciones a cargo del empleado
        Stations = Station.objects.filter(employee=SMaster)

        # action es la accion a realizar
        # y bike_id es la bicileta a la cual aplicar
        if request.method == 'POST':
            bike_id = request.POST.get('bike_id')
            action = request.POST.get('Action')
            try:
                bike = Bike.objects.get(id=bike_id)
                if action == 'Repair':
                    bike.state = 'AV'
                    messages.success(request, 'Bike Repaired!')
                elif action == 'Set As Broken':
                    bike.state = 'BR'
                    messages.success(request, 'Bike Not Longer Available!')
                bike.save()
            except Bike.DoesNotExist:
                messages.error(request, 'Select A Bike!')

        # obtener solo las bicis rotas que estan
        # en estaciones a cargo del empleado
        try:
            context = dict()
            context['brokenbikes'] = []
            context['availablebikes'] = []
            for S in Stations:
                filterargsA = {'state': 'AV', 'station': S}
                available = Bike.objects.filter(**filterargsA)
                context['availablebikes'].extend(list(available))
                filterargsB = {'state': 'BR', 'station': S}
                broken = Bike.objects.filter(**filterargsB)
                context['brokenbikes'].extend(list(broken))
        except Bike.DoesNotExist:
            messages.error(request, 'Not Are Bikes Here')

        return render(request, 'Sbike/set_bike_status.html', context)
    except Employee.DoesNotExist:
        messages.error(
            request, 'This Content is Unavailable!')
        return redirect('/stationprofile')

# ##-----------------------------------------------------------------------## #
# ##------------------------END-SET-BIKE-STATUS----------------------------## #
# ##-----------------------------------------------------------------------## #


# ##-----------------------------------------------------------------------## #
# ##-------------------------CREATE--STATION-------------------------------## #
# ##-----------------------------------------------------------------------## #

@login_required
def createStation(request):
    user_type = request.session['user_type']

    if user_type == 'admin':
        if request.method == 'POST':
            form = CreateStationForm(request.POST)
            if form.is_valid():
                cleaned_data = form.cleaned_data

                name = form.clean_name()
                address = form.clean_address()
                capacity = cleaned_data.get('capacity')

                station = Station()
                station.create_station(name, address, capacity)
                messages.success(request, 'Station Successfully Created!')
                return redirect('/webprofile')
            else:
                messages.error(request, 'Station Name / Adress Exists Already')

                return redirect('/createstation')

        form = CreateStationForm()
        context = {
            'form': form,
        }

        return render(request, 'Sbike/create_station.html', context)

    else:
        messages.error(request, 'This Content is Unavailable!')
        return redirect('/webprofile')

# ##-----------------------------------------------------------------------## #
# ##-------------------------END--CREATE--STATION--------------------------## #
# ##-----------------------------------------------------------------------## #


# ##-----------------------------------------------------------------------## #
# ##---------------------ASSIGN--EMPLOYEE-TO-STATION-----------------------## #
# ##-----------------------------------------------------------------------## #


@login_required
def assignEmployee(request):
    user_type = request.session['user_type']

    if user_type == 'admin':
        if request.method == 'POST':
            try:
                employee_dni = request.POST.get('selectemployee')
            except IntegrityError:
                messages.error(request, 'Error! 123!')
            finally:
                request.session['employee_to_assign'] = int(employee_dni)
                return redirect('/assignstation')

        employees = Employee.objects.all()
        if len(employees) == 0:
            messages.error(request, 'Sorry, No Employees!')
        return render(
            request, 'Sbike/assign_employee.html', {'employees': employees})
    else:
        messages.error(request, 'This Content is Unavailable!')
        return redirect('/webprofile')


@login_required
def assignStation(request):
    user_type = request.session['user_type']

    if user_type == 'admin':
        if request.method == 'POST':
            try:
                station_id = request.POST.get('selectstation')
                employee = Employee.objects.filter(
                    dni=int(request.session['employee_to_assign']))
                station = Station.objects.filter(id=station_id)
                station.update(employee=employee[0])
                employee.update(is_assigned=True)
            except IntegrityError:
                messages.error(request, 'Error! 123!')
            finally:
                msg0 = 'Employee Assigned: ' + str(employee[0].user)
                msg = msg0 + ' - Station: ' + str(station[0].name)
                messages.success(request, msg)
                return redirect('/webprofile')

        stations = Station.objects.filter(employee__isnull=True)
        if len(stations) == 0:
            messages.error(request, 'Sorry, No Free Stations!')
        return render(
            request, 'Sbike/assign_station.html', {'stations': stations})
    else:
        messages.error(request, 'This Content is Unavailable!')
        return redirect('/webprofile')


# ##-----------------------------------------------------------------------## #
# ##----------------END--ASSIGN--EMPLOYEE-TO-STATION-----------------------## #
# ##-----------------------------------------------------------------------## #

# ##-----------------------------------------------------------------------## #
# ##-----------------UNASSIGN--EMPLOYEE-FROM-STATION-----------------------## #
# ##-----------------------------------------------------------------------## #

@login_required
def unassignEmployee(request):
    user_type = request.session['user_type']

    if user_type == 'admin':
        if request.method == 'POST':
            try:
                employee_dni = request.POST.get('selectemployee')
            except IntegrityError:
                messages.error(request, 'Error! 123!')
            finally:
                request.session['employee_to_unassign'] = int(employee_dni)
                return redirect('/unassignstation')

        employees = Employee.objects.filter(is_assigned=True)
        if len(employees) == 0:
            messages.error(request, 'Sorry, No Employees Assigned!')
        return render(
            request, 'Sbike/unassign_employee.html', {'employees': employees})
    else:
        messages.error(request, 'This Content is Unavailable!')
        return redirect('/webprofile')


@login_required
def unassignStation(request):
    user_type = request.session['user_type']

    if user_type == 'admin':
        if request.method == 'POST':
            try:
                station_id = request.POST.get('selectstation')
                employee = Employee.objects.filter(
                    dni=int(request.session['employee_to_unassign']))
                station = Station.objects.filter(id=station_id)
                station.update(employee=None)
                if (request.session['stations_assigned'] == 1):
                    employee.update(is_assigned=False)
            except IntegrityError:
                messages.error(request, 'Error! 123!')
            finally:
                msg0 = 'Employee Unassigned: ' + str(employee[0].user)
                msg = msg0 + ' - Station: ' + str(station[0].name)
                messages.success(request, msg)
                return redirect('/webprofile')

        employee = Employee.objects.filter(
            dni=int(request.session['employee_to_unassign']))
        stations = Station.objects.filter(employee=employee)
        request.session['stations_assigned'] = len(stations)
        if len(stations) == 0:
            # No deberia ocurrir nunca
            messages.error(request, 'Sorry, No Assigned Stations!')
        return render(
            request, 'Sbike/unassign_station.html', {'stations': stations})
    else:
        messages.error(request, 'This Content is Unavailable!')
        return redirect('/webprofile')

# ##-----------------------------------------------------------------------## #
# ##-----------------END--UNASSIGN--EMPLOYEE-FROM-STATION------------------## #
# ##-----------------------------------------------------------------------## #

# ##-----------------------------------------------------------------------## #
# ##---------------------------VIEW_CLIENTS--------------------------------## #
# ##-----------------------------------------------------------------------## #


@login_required
def viewClients(request, username=''):

    if username:
        clients = Client.objects.filter(user__username=username)
        if clients.first() is not None:
            return clientProfile(request, clients[0], readOnly=True)
        else:
            return render(request, 'Sbike/view_clients.html',
                          {'message': 'The user "' +
                           username + '" does not exist'})

    user_type = request.session['user_type']

    if user_type == 'admin':
            clients = Client.objects.all()
            clients2 = []
            for cli in clients:
                cliente = createUserDict(cli)
                sanction = Sanction.objects.filter(client=cli).first()
                cliente['sanction'] = sanction is not None
                clients2.append(cliente)

            return render(
                request, 'Sbike/view_clients.html', {'clients': clients2})

    else:
        messages.error(request, 'This Content is Unavailable!')
        return redirect('/webprofile')


# ##-----------------------------------------------------------------------## #
# ##--------------------------END--VIEW_CLIENTS----------------------------## #
# ##-----------------------------------------------------------------------## #


# ##-----------------------------------------------------------------------## #
# ##----------------------------ADD-BIKE-----------------------------------## #
# ##-----------------------------------------------------------------------## #
def addBike(request):

    if request.session['user_type'] == 'admin':
        if request.method == 'POST':
            stationD = request.POST.get('select')
            bikeamount = request.POST.get('input')
            stationDes = Station.objects.filter(id=stationD)[0]
            stockAll = stationDes.total_stock()

            if bikeamount == '':
                messages.error(request, 'Please Enter a Number')
                return redirect('/addbikes')

            try:
                if (stockAll + int(bikeamount)) <= stationDes.capacity:
                    for i in range(0, int(bikeamount)):
                        bike = Bike()
                        bike.station = stationDes
                        bike.save()
                    messages.success(
                        request,
                        str(i+1) + ' Bikes Created In ' + stationDes.name)
                    return redirect('/webprofile')
                else:
                    msg0 = ' Just Have ' + str(stationDes.capacity - stockAll)
                    msg = msg0 + ' Spaces Empty'
                    messages.error(
                        request, 'The Station ' + stationDes.name + msg)

            except UnboundLocalError:
                messages.error(request, 'Invalid Input For Amount')

        station = Station.objects.all()

        if len(station) == 0:
            messages.error(request, 'There Is No Created Stations!!')
            return redirect('/webprofile')

        return render(request, 'Sbike/add_bike.html', {'stations': station})

    messages.error(request, 'This Content is Unavailable!')
    if request.session['type'] == 'station':
        return redirect('/stationprofile')
    return redirect('/webprofile')
# ##-----------------------------------------------------------------------## #
# ##--------------------------END-ADD-BIKE---------------------------------## #
# ##-----------------------------------------------------------------------## #


# ##-----------------------------------------------------------------------## #
# ##------------------------REGISTER--EMPLOYEE-----------------------------## #
# ##-----------------------------------------------------------------------## #

@login_required
def employeeRegister(request):
    user_type = request.session['user_type']
    if user_type == 'admin':
        if request.method == 'POST':
            form = RegisterForm(request.POST)

            if form.is_valid():
                cleaned_data = form.cleaned_data
                username = cleaned_data.get('username')
                password = cleaned_data.get('password1')
                first_name = cleaned_data.get('first_name')
                last_name = cleaned_data.get('last_name')
                email = cleaned_data.get('email')
                phone_number = cleaned_data.get('phone_number')
                dni = cleaned_data.get('dni')

                user = User.objects.create_user(username, email, password)

                user.first_name = first_name
                user.last_name = last_name

                user.save()

                employee = Employee()
                employee.user = user
                employee.phone_number = phone_number
                employee.dni = dni

                employee.save()

                messages.success(
                    request, 'You Have Successfully Registered An Employee')

                return redirect('/webprofile')

        else:
            form = RegisterForm()
        context = {
            'form': form
        }

        return render(request, 'Sbike/employee_register.html', context)

    else:
        messages.error(request, 'This Content is Unavailable!')
        return redirect('/webprofile')


# ##-----------------------------------------------------------------------## #
# ##-------------------END--REGISTER--EMPLOYEE-----------------------------## #
# ##-----------------------------------------------------------------------## #

# ##-----------------------------------------------------------------------## #
# ##------------------------EMPLOYEE--CONSULT--HIS--STATIONS---------------## #
# ##-----------------------------------------------------------------------## #

@login_required
def employeeConsult(request):
    employee_consult = Employee.objects.get(user=request.user)
    station_consult = Station.objects.filter(employee=employee_consult)
    bikes = Bike.objects.filter(station=station_consult)
    return render(request, 'Sbike/employee_consult.html', {'bikes': bikes})

# ##-----------------------------------------------------------------------## #
# ##-------------------END--EMPLOYEE--CONSULT--HIS--STATIONS---------------## #
# ##-----------------------------------------------------------------------## #

# ##-----------------------------------------------------------------------## #
# ##-----------------------------MOVE--BIKES-------------------------------## #
# ##-----------------------------------------------------------------------## #


@login_required
def moveBike(request):
    if (request.session['user_type'] == 'admin'):
        if request.method == 'POST':

            station_from_id = request.POST.get('select_from')
            station_to_id = request.POST.get('select_to')
            bikes_to_move = request.POST.get('max_bikes')

            if station_from_id is not None:
                station_from = Station.objects.filter(
                    id=station_from_id).first()
                request.session['station_from'] = station_from_id

                stations_to = Station.objects.all()
                stations_to = stations_to.exclude(id=station_from_id)
                return render(
                    request, 'Sbike/move_bike.html',
                    {'stations_to': stations_to})

            if station_to_id is not None:
                station_to = Station.objects.filter(id=station_to_id).first()
                request.session['station_to'] = station_to_id

                capacity_to = station_to.capacity
                stock_to = station_to.total_stock()
                station_from = Station.objects.filter(
                    id=request.session['station_from']).first()
                max_bikes_from = station_from.stock()
                bikes = capacity_to - stock_to - max_bikes_from
                if bikes < 0:
                    max_bikes = capacity_to - stock_to
                else:
                    max_bikes = max_bikes_from

                return render(
                    request, 'Sbike/move_bike.html',
                    {'max_bikes': list(range(max_bikes + 1))})

            if bikes_to_move is not None:
                station_from = Station.objects.filter(
                    id=request.session['station_from']).first()
                station_to = Station.objects.filter(
                    id=request.session['station_to']).first()
                args = {'state': 'AV', 'station': station_from}
                bikes = Bike.objects.filter(**args)[:int(bikes_to_move)]
                for bike in bikes:
                    bike.station = station_to
                    bike.save()
                messages.success(request, str(bikes_to_move) + 'Bikes Moved!')
                return redirect('/webprofile')

        stations_from = Station.objects.all()
        return render(
            request, 'Sbike/move_bike.html', {'stations_from': stations_from})

    else:
        messages.error(request, 'Access Restricted Only To Admin!')
        if (request.session['type'] == 'web'):
            return redirect('/webprofile')
        else:
            return redirect('/stationprofile')

# ##-----------------------------------------------------------------------## #
# ##------------------------END--MOVE--BIKES-------------------------------## #
# ##-----------------------------------------------------------------------## #


# ##-----------------------------------------------------------------------## #
# ##------------------------ABOUT-STATEBIKES-------------------------------## #
# ##-----------------------------------------------------------------------## #


def about(request):
    return render(request, 'Sbike/about.html')
# ##-----------------------------------------------------------------------## #
# ##------------------------ABOUT-STATEBIKES-------------------------------## #
# ##-----------------------------------------------------------------------## #

# ##-----------------------------------------------------------------------## #
# ##-------------------------------CONTACT---------------------------------## #
# ##-----------------------------------------------------------------------## #


def contact(request):
    return render(request, 'Sbike/contact.html')
# ##-----------------------------------------------------------------------## #
# ##-----------------------------END--CONTACT------------------------------## #
# ##-----------------------------------------------------------------------## #
