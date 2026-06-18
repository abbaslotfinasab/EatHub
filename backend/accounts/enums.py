from django.db import models


class RoleCode(models.TextChoices):
    OWNER = "OWNER", "Owner"
    MANAGER = "MANAGER", "Manager"
    CASHIER = "CASHIER", "Cashier"
    CHEF = "CHEF", "Chef"
    WAITER = "WAITER", "Waiter"
    ACCOUNTANT = "ACCOUNTANT", "Accountant"



class InvitationStatus(models.TextChoices):
    PENDING = "PENDING", "Pending"
    ACCEPTED = "ACCEPTED", "Accepted"
    EXPIRED = "EXPIRED", "Expired"
    REVOKED = "REVOKED", "Revoked"



class MembershipStatus(models.TextChoices):
    ACTIVE = "ACTIVE", "Active"
    INACTIVE = "INACTIVE", "Inactive"
    SUSPENDED = "SUSPENDED", "Suspended"




S_CREATE = "employees.create", "Create Employees"