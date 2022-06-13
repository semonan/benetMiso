from django.shortcuts import render
from .babyMonitoring import babyMonitor
from django.http import HttpResponse, JsonResponse, FileResponse
from django.http import JsonResponse
import json


# Create your views here.
def index(request):
    return render(request, 'main/index.html')


def temperature_max(request):
    result = {
        "temperature_max" : babyMonitor.getTemperatureMax(),
    }
    return JsonResponse(result)


def current_capture(request):
    try:
        img = open('capture/currentCapture.png', 'rb')
    except IOError as msg:
        print(msg)

    return FileResponse(img)