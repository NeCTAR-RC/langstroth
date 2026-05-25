from django.shortcuts import render
from django.views.decorators.csrf import requires_csrf_token


@requires_csrf_token
def handler500(request):
    return render(
        request,
        "error.html",
        {
            "title": "ERROR: Internal Server Error",
            "message": (
                "An unhandled error has occurred. Our staff have been "
                "notified."
            ),
        },
        status=500,
    )


@requires_csrf_token
def handler400(request, exception):
    return render(
        request,
        "error.html",
        {
            "title": "ERROR: Bad Request",
            "message": "The request could not be understood by the server.",
        },
        status=400,
    )
