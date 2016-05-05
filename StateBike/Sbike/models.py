from django.db import models
from django.contrib.auth.models import User
from datetime import datetime, timedelta
from django.utils import timezone


class SBikeUser(models.Model):
    user = models.OneToOneField(User)
    dni = models.IntegerField(blank=False, primary_key=True)
    phone_number = models.IntegerField(null=True, blank=True)

    def __str__(self):
        return "User: " + str(self.user.username)

    def edit_phone(self, phone):
        self.phone_number = phone
        self.save()

    def edit_email(self, email):
        self.user.email = email
        self.user.save()


class Client(SBikeUser):
    card_number = models.IntegerField(blank=False, null=True)
    expiration_date = models.DateField(blank=False, null=True)
    security_code = models.IntegerField(blank=False, null=True)

    def edit_card(self, card_number, expiration_date, security_code):
        self.card_number = card_number
        self.expiration_date = expiration_date
        self.security_code = security_code
        self.save()

    def __str__(self):
        return str(self.user.username)


class Admin(SBikeUser):
    def __str__(self):
        return str(self.user.username)
    pass


class Employee(SBikeUser):
    is_assigned = models.BooleanField(default=False)

    def __str__(self):
        return str(self.user.username)


class Station(models.Model):
    employee = models.ForeignKey(Employee, null=True, blank=True)
    name = models.CharField(max_length=200)
    address = models.CharField(max_length=200)
    capacity = models.IntegerField(blank=False)

    def __str__(self):
        return str(self.name)

    def create_station(self, name, address, capacity):
        self.name = name
        self.address = address
        self.capacity = capacity
        self.save()

    def assign_employee(self, employee):
        self.employee = employee
        self.save()

    def stock(self):
        args = {'state': 'AV', 'station': self}
        return len(Bike.objects.filter(**args))

    def total_stock(self):
        return len(Bike.objects.filter(station=self))


class Bike(models.Model):
    AVAILABLE = 'AV'
    TAKEN = 'TK'
    BROKEN = 'BR'

    STATE_CHOICES = (
        (AVAILABLE, 'Available'),
        (TAKEN, 'Taken'),
        (BROKEN, 'Broken'),
    )

    state = models.CharField(
        max_length=2, choices=STATE_CHOICES,
        default=AVAILABLE)

    station = models.ForeignKey(Station)

    def __str__(self):
        return "Bike: " + str(self.id)

    def move(self, station):
        self.station = station
        self.save()

    def take(self):
        self.state = 'TK'
        self.save()

    def repair(self):
        self.state = 'AV'
        self.save()

    def give_back(self):
        self.state = 'AV'
        self.save()


class Loan(models.Model):
    client = models.OneToOneField(Client)
    bike = models.OneToOneField(Bike)
    startDate = models.DateTimeField(default=datetime.now)
    endDate = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return "Loan: " + str(self.id)

    def create_loan(self, client, bike):
        self.client = client
        self.bike = bike
        self.save()

    def set_end_date(self):
        self.endDate = timezone.now()
        self.save()

    def eval_sanction(self):
        dt = self.endDate - self.startDate
        return dt.days


class Sanction(models.Model):
    client = models.OneToOneField(Client)
    loan = models.OneToOneField(Loan)
    amount = models.DecimalField(
        max_digits=6, decimal_places=2, null=True, blank=True)
    is_minor = models.BooleanField()
    date = models.DateTimeField(null=True, blank=True)
    deposition = models.TextField(null=True, blank=True)

    def create_sanction(self, loan, days):
        self.loan = loan
        self.client = self.loan.client
        self.is_minor = days == 1
        self.date = self.loan.endDate
        self.save()

    def generate_deposition(self, deposition):
        self.deposition = deposition
        self.save()

    def is_over(self):
        days = timedelta(days=5)
        dt = self.date + days
        return dt <= timezone.now()


class Notification(models.Model):
    station = models.OneToOneField(Station)
    date = models.DateTimeField(default=datetime.now)

    def add_station(self, station):
        self.station = station
        self.save()
