from django.http import HttpResponse


def index(request):
    return HttpResponse("Hello, world. You're at the polls index.")

def detail(request, event_id):
    return HttpResponse("This is event %s" % event_id)