from django.urls import path
from restapp.views import *
from restapp import views
urlpatterns = [
    path('',views.home,name="home"),
    path('users/register/',views.registerUser,name="register"),
    # path('activate/<uidb64>/<token>',views.ActivateAccountView.as_view(),name='activate'),
    path('activate/<uidb64>/<token>',views.activateAccount,name='activate'),
]
