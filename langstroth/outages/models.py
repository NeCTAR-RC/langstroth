from django.db import models


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
    outage = models.ForeignKey(Outage)
    content = models.TextField()
