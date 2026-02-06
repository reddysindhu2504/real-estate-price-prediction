from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
import random


# -------------------------
# REALTOR MODEL
# -------------------------
class Realtor(models.Model):
    name = models.CharField(max_length=200)
    phone = models.CharField(max_length=50, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    state = models.CharField(max_length=120, blank=True, null=True)
    district = models.CharField(max_length=120, blank=True, null=True)
    locality = models.CharField(max_length=200, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def _str_(self):
        return f"{self.name} - {self.district}, {self.state}"


# -------------------------
# CONSTRUCTION QUERY MODEL
# -------------------------
class PropertyQuery(models.Model):
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    country = models.CharField(max_length=100, default="India")
    state = models.CharField(max_length=120)
    district = models.CharField(max_length=120)
    location = models.CharField(max_length=255, blank=True, null=True)
    size_sqft = models.FloatField()
    bedrooms = models.IntegerField()
    bathrooms = models.IntegerField()
    age = models.IntegerField()
    amenities_score = models.FloatField(default=0.0)
    monthly_income = models.FloatField(null=True, blank=True)
    predicted_price = models.FloatField(null=True, blank=True)
    cluster = models.IntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def _str_(self):
        return f"{self.state} / {self.district} - ₹{self.predicted_price}"


# -------------------------
# LAND QUERY MODEL (ANN / DL)
# -------------------------
class LandQuery(models.Model):
    land_shape=models.CharField(max_length=50)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    state = models.CharField(max_length=100)
    district = models.CharField(max_length=100)
    land_area = models.FloatField()
    soil_type = models.CharField(max_length=50)
    road_width = models.FloatField()
    land_shape = models.CharField(max_length=50)
    predicted_price = models.FloatField()
    created_at = models.DateTimeField(auto_now_add=True)



class LoginHistory(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    login_time = models.DateTimeField(auto_now_add=True)
    logout_time = models.DateTimeField(null=True, blank=True)
    ip_address = models.CharField(max_length=45, blank=True, null=True)

    def __str__(self):
        return f"{self.user.username} - {self.login_time}"