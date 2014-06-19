from django.shortcuts import render
from django.views.decorators.csrf import requires_csrf_token


@requires_csrf_token
def handler500(request):
    return render(request, "error.html",
                  {"title": "ERROR: Internal Server Error",
                   "message": "An unhandled error has occured.  Our staff have been emailed."})
