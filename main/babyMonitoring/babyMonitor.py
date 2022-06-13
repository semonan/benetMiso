from . import leptonCapture


def getTemperatureMax():
    value = leptonCapture.getHighCelcius()
    if value is None:
        return 'null'
    else:
        return value