from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager

# Create your models here.
class CustomUserManager(BaseUserManager):
    def create_user(self,username,password=None):
        if not username:
            raise ValueError("Username Required")
        user = self.model(username=username)
        user.set_password(password)   
        user.save(using=self._db)
        return user
    
    def create_superuser(self,username,password=None):
        user = self.create_user(username=username,password=password)
        user.is_admin = True
        user.save(using=self._db)
        return user
    

class MyUserTable(AbstractBaseUser):
    username= models.CharField(max_length=50,unique=True)
    email= models.CharField(max_length=50,null=True)
    first_name= models.CharField(max_length=20,null=True)
    last_name= models.CharField(max_length=20,null=True)
    is_admin = models.BooleanField(default=0)
    is_active= models.BooleanField(default=0)
    # verification_sent_at = models.DateTimeField(null=True, blank=True)

    USERNAME_FIELD = "username"

    REQUIRED_FIELDS = []
    
    objects = CustomUserManager()

    def has_perm(self, perm, obj=None):
        return True

    def has_module_perms(self, app_label):
        return True
    @property
    def is_staff(self):
        return self.is_admin