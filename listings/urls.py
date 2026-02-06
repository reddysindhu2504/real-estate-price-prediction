from django.urls import path
from . import views
from django.contrib.auth import views as auth_views
from .views_land import land_prediction
from . import views_land
from django.contrib.auth import views as auth_views




urlpatterns = [

    # landing + auth
    path('', views.landing, name='landing'),
    path('signup/', views.signup, name='signup'),
    
    path('login/', auth_views.LoginView.as_view(
        template_name='registration/login.html',
        redirect_authenticated_user=True
    ), name='login'),
    path('logout/', views.logout_view, name='logout'),
    

    # choose page
    path('choose/', views.choose, name='choose'),

    # ---------------- CONSTRUCTION ----------------
    path('home/', views.index, name='home'),              # construction home
    path('history/', views.history, name='history'),      # construction history
    path('dashboard/', views.dashboard, name='dashboard'),

    # ---------------- LAND ----------------
    path("land/",views.land_prediction, name="land"),

    #path('land/', views.land_home, name='land'),
    path('land/history/', views.land_history, name='land_history'),
    path("land/details/", views.land_details, name="land_details"),
    path("land/dashboard/", views.land_dashboard, name="land_dashboard"),

    # static
    path('details/', views.details, name='details'),
    path('about/', views.about, name='about'),
        path(
        "password-reset/",
        auth_views.PasswordResetView.as_view(
            template_name="registration/password_reset.html"
        ),
        name="password_reset"
    ),

    path(
        "password-reset/done/",
        auth_views.PasswordResetDoneView.as_view(
            template_name="registration/password_reset_done.html"
        ),
        name="password_reset_done"
    ),

    path(
        "reset/<uidb64>/<token>/",
        auth_views.PasswordResetConfirmView.as_view(
            template_name="registration/password_reset_confirm.html"
        ),
        name="password_reset_confirm"
    ),

    path(
        "reset/done/",
        auth_views.PasswordResetCompleteView.as_view(
            template_name="registration/password_reset_complete.html"
        ),
        name="password_reset_complete"
    ),


]
