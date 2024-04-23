import requests
import json
import num2words


def get_weather():
    api_key = '6baf79a0e633c55b66bbab676ae89d95'
    link = f'https://api.openweathermap.org/data/2.5/weather?lat=52.95478319999999&lon=-1.1581085999999914&appid={api_key}'
    r = requests.get(url=link).text
    data = json.loads(r)
    weather_description = data["weather"][0]["description"]
    temperature_celsius = round(data["main"]["temp"] - 273.15)
    temperature_text = num2words.num2words(temperature_celsius)
    return weather_description, temperature_text

