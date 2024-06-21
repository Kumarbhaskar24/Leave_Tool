from django.contrib import admin
from .models import LeaveBalance, LeaveHistory

class LeaveBalanceAdmin(admin.ModelAdmin):
    list_display = ('employee_id', 'sick_leave', 'paid_leave', 'unpaid_leave') 

class LeaveHistoryAdmin(admin.ModelAdmin):
    list_display = ('employee', 'type_of_leave', 'start_date', 'end_date', 'leave_count', 'leave_balance')
    search_fields = ('employee__employee_id', 'type_of_leave')
    list_filter = ('type_of_leave', 'start_date', 'end_date')

admin.site.register(LeaveBalance, LeaveBalanceAdmin)
admin.site.register(LeaveHistory, LeaveHistoryAdmin)
