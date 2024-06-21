from django.db import models

class LeaveBalance(models.Model):
    employee_id = models.CharField(max_length=20, unique=True, default='abcd')
    manager = models.ForeignKey('self', null=True, blank=True, on_delete=models.SET_NULL, related_name='subordinates')
    sick_leave = models.IntegerField(default=0)
    paid_leave = models.IntegerField(default=0)
    unpaid_leave = models.IntegerField(default=0)

    def __str__(self):
        return self.employee_id

class LeaveHistory(models.Model):
    employee = models.ForeignKey(LeaveBalance, on_delete=models.CASCADE)
    type_of_leave = models.CharField(max_length=20)
    start_date = models.DateField()
    end_date = models.DateField()
    leave_count = models.IntegerField()
    leave_balance = models.IntegerField()

    def __str__(self):
        return f"{self.employee.employee_id} - {self.type_of_leave} - {self.start_date} to {self.end_date}"
