from django.db import models
from django.contrib.auth.models import AbstractUser

# Custom User Model
class CustomUser(AbstractUser):
    ROLE_CHOICES = [
        ('Admin', 'Admin'),
        ('Research', 'Research'),
        ('Analyst', 'Analyst'),
    ]
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='Admin')

    def __str__(self):
        return f"{self.username} ({self.role})"


# Region Model
class Region(models.Model):
    REGION_TYPE_CHOICES = [
        ('Town', 'Town'),
        ('Forest Land', 'Forest Land'),
        ('Way', 'Way'),
        ('Healthy Forest', 'Healthy Forest'),
        ('Homes', 'Homes'),
    ]

    name = models.CharField(max_length=100, unique=True)
    region_type = models.CharField(max_length=50, choices=REGION_TYPE_CHOICES)

    def __str__(self):
        return f"{self.name} ({self.region_type})"

# Town Model (Linked to Region)
class Town(models.Model):
    region = models.ForeignKey(Region, on_delete=models.CASCADE)
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name

# LandType Model (Linked to Town)
class LandType(models.Model):
    LAND_CHOICES = [
        ('Forest Land', 'Forest Land'),
        ('Way', 'Way'),
        ('Healthy Forest', 'Healthy Forest'),
        ('Homes', 'Homes'),
    ]

    town = models.ForeignKey(Town, on_delete=models.CASCADE)
    land_type = models.CharField(max_length=50, choices=LAND_CHOICES)

    def __str__(self):
        return f"{self.land_type} in {self.town.name}"


class ImageAnalysis(models.Model):
    region = models.CharField(max_length=100)
    identifications = models.TextField()
    image = models.ImageField(upload_to='region_images/', null=True, blank=True)
    is_deforested = models.BooleanField(default=False)

    def __str__(self):
        return self.region
    
class Result(models.Model):
    region= models.CharField(max_length=50)     
    prediction = models.TextField()   
    image = models.ImageField(upload_to='result_images/')        
    
    def __str__(self):
        return f"{self.region} - {self.type}"
    
