import urllib.request, urllib.error, urllib.parse, json
import requests
from flask import Flask, render_template, request
import logging

app = Flask(__name__)

def safe_get(url):
    try:
        return urllib.request.urlopen(url)
    except urllib.error.HTTPError as e:
        print("The server couldn't fulfill the request.")
        print(url)
        print("Error code: ", e.code)
    except urllib.error.URLError as e:
        print("We failed to reach a server")
        print(url)
        print("Reason: ", e.reason)
    return None

def pretty(obj):
    return json.dumps(obj, sort_keys=True, indent=2)

@app.route("/")
def main_handler():
    app.logger.info("In MainHandler")
    return render_template('get_user_input.html',page_title="Travel Form")

url = "https://weatherapi-com.p.rapidapi.com/forecast.json"
def forecast_weather(location):
    querystring = {"q": location, "days": "7"}
    headers = {
        'x-rapidapi-host': "weatherapi-com.p.rapidapi.com",
        'x-rapidapi-key': "5af58ad3e2msh6fa59a7265f9571p101d5djsn359c9e7638ec"
    }
    response = requests.request("GET", url, headers=headers, params=querystring)
    dict = response.json()
    return dict

def weather_output(dictt):
    location = '<h1>' + dictt['location']['name'] + '</h1>'
    day_info = ''
    day = 1
    for value in dictt['forecast']['forecastday']:
        day_info += '<b>' + "day: " + str(day) + '</b>'+ "\n" + "highest temperature: " + str(value['day']['maxtemp_c']) + "celsius" + "\n" + "lowest temperature: " + str(value['day']['mintemp_c']) + "celsius" + "\n" + "maximum wind degree: " + str(value['day']['maxwind_mph']) + "mph" + "\n" + "humidity: " + str(value['day']['avghumidity']) + "\n"
        day += 1
    result = location + "\n" + day_info
    result = result.replace("\n","<br>")
    return result

def travel_recommendation(dicttt):
    for infomation in dicttt['forecast']['forecastday']:
        if infomation['day']['daily_chance_of_rain'] > 50:
            return "Recommendation: It will probably rain on next three days, not a good time to visit this place."
    return "Recommendation：the weather is good, recommend to go!"

import flickr_key as flickr_key
def flickrREST(baseurl = 'https://api.flickr.com/services/rest/',
    method = 'flickr.photos.search',
    api_key = flickr_key.key,
    format = 'json',
    params={},
    printurl = False
    ):
    params['method'] = method
    params['api_key'] = api_key
    params['format'] = format
    if format == "json": params["nojsoncallback"]=True
    url = baseurl + "?" + urllib.parse.urlencode(params)
    if printurl:
        print(url)
    return safe_get(url)

def get_photo_ids(tag, n=100):
    dictt = flickrREST(params={"tags":tag, "per_page":n}, printurl=True)
    dict_jon = json.loads(dictt.read())
    result = []
    for value in dict_jon['photos']['photo']:
        result.append(value.get("id"))
    return result

def get_photo_info(photo_id):
    temp_dict = flickrREST(method='flickr.photos.getInfo', params={"photo_id":photo_id}, printurl=True)
    result_dict = json.loads(temp_dict.read())
    return result_dict

class FlickrPhoto():
    def __init__(self, dict):
        self.title = dict["photo"]["title"]["_content"]
        self.author = dict["photo"]['owner']['username']
        self.userid = dict["photo"]['owner']['nsid']
        self.tags = [x['_content'] for x in dict["photo"]['tags']['tag']]
        self.comments = dict['photo']['comments']['_content']
        self.views = dict["photo"]["views"]
        self.url = dict["photo"]["urls"]["url"][0]["_content"]
        self.server = dict["photo"]["server"]
        self.id = dict["photo"]["id"]
        self.secret = dict["photo"]["secret"]

    def make_photo_url(self, size='q'):
        if size != None:
            return "https://live.staticflickr.com/" + str(self.server) + "/" + str(self.id) + "_" + self.secret + "_" + size + ".jpg"
        else:
            return "https://live.staticflickr.com/" + str(self.server) + "/" + str(self.id) + "_" + self.secret + ".jpg"

    def __str__(self):
        result = "~~~ " + self.title + " ~~~" + "\n" + "author: " + self.author + "\n" + "number of tags: " + str(len(self.tags)) + "\n" + "views: " + str(self.views) + "\n" + "comments: " + str(self.comments) + "\n" + "url: " + str(self.url)
        return result

@app.route("/gresponse")
def greet_response_handler():
    app.logger.info(request.args.get('city_name'))
    name = request.args.get('city_name')
    if name:
        dict_weather = forecast_weather(name)
        if dict_weather.get("error"):
            return render_template('get_user_input.html',
                                   page_title="Weather Form - Error",
                                   prompt="How can I give you weather forecast if you don't enter a city's name?")
        else:
            list_ids = get_photo_ids(name, 10)
            list_object = [FlickrPhoto(get_photo_info(x)) for x in list_ids]
            sorted_list = sorted(list_object, key=lambda x: int(x.views), reverse=True)
            recommendation = travel_recommendation(dict_weather)
            return render_template('get_response.html',
                                   name=name,
                                   page_title="Weather Page Response for %s"%name,
                                   greetings=weather_output(dict_weather),
                                   photos=sorted_list[:5],
                                   recommend=recommendation
                                   )
    else:
        return render_template('get_user_input.html',
                               page_title="Weather Form - Error",
                               prompt="How can I give you weather forecast if you don't enter a city's name?")

if __name__ == "__main__":
    app.run(host="localhost", port=1100, debug=True)