


from django.contrib import admin
from .models import Realtor, PropertyQuery

@admin.register(Realtor)
class RealtorAdmin(admin.ModelAdmin):
    list_display = ('name','phone','state','district','locality')
    search_fields = ('name','state','district','locality')

@admin.register(PropertyQuery)
class PropertyQueryAdmin(admin.ModelAdmin):
    list_display = ('location','state','district','size_sqft','predicted_price','created_at')
    list_filter = ('state','district')
    search_fields = ('location','state','district')


from .models import LoginHistory

@admin.register(LoginHistory)
class LoginHistoryAdmin(admin.ModelAdmin):
    list_display = ("user", "login_time", "logout_time", "ip_address")
    list_filter = ("login_time",)