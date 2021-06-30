from django.db import models



#The Outages Severity Rating (OSR):
#Negligible – This is a negligible outage, recorded and reported but with little or no obvious impact on business services, and no service disruptions
#Minimal – This is a minimal outage where some number of IT business services are disrupted or degraded but with minimal effect on users/customers/reputation.
#Significant – This is a significant outage, with observable customer/user services disruptions, mainly of limited scope, duration or effect. Minimal or no financial effect. Some reputational or compliance impact(s) possible.
#Serious – This is a serious outage, with disruption of service and/or operations. Ramifications include some financial losses, compliance breaches, damage to reputation, and possible safety concerns.
#Severe – This is a mission critical outage, with major, damaging disruption of services and/or operations with ramifications including large financial losses, possible safety issues, compliance breaches, customer losses and reputational damage.


class Outage(models.Model):
    SCHEDULED = 'S'
    INVESTIGATING = 'IN'
    IDENTIFIED = 'ID'
    WATCHING = 'W'
    FIXED = 'F'
    STATUS_CHOICES = [
        (SCHEDULED, 'Scheduled'),
        (INVESTIGATING, 'Investigating'),
        (IDENTIFIED, 'Identified'),
        (WATCHING, 'Watching'),
        (FIXED, 'Fixed'),
    ]
    NEGLIGIBLE = 1
    MINIMAL = 2
    SIGNIFICANT = 3
    SERIOUS = 4
    SEVERE = 5
    SEVERITY_CHOICES = [
        (NEGLIGIBLE, 'Negligible'),
        (MINIMAL, 'Minimal'),
        (SIGNIFICANT, 'Significant'),
        (SERIOUS, 'Serious'),
        (SEVERE, 'Severe'),
    ]
    title = models.CharField(max_length=255)
    description = models.TextField()
    status = models.CharField(max_length=2, choices=STATUS_CHOICES)
    start = models.DateTimeField()
    end = models.DateTimeField()
    severity = models.IntegerField(choices=SEVERITY_CHOICES)



class OutageComment(models.Model):
    time = models.DateTimeField(auto_now_add=True)
    outage = models.ForeignKey(Outage, on_delete=models.CASCADE)
    content = models.TextField()
