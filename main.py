"""`main` is the top level module for your Flask application."""


from flask import Flask
from flask import render_template
from google.appengine.ext import ndb
from flask import request
import json
import time
from collections import OrderedDict


app = Flask(__name__)
app.debug = True


class dtModel(ndb.Model):
    json_data = ndb.JsonProperty()
    name = ndb.StringProperty()


def getting_json(json_name):
    val = dtModel.query(dtModel.name == json_name).fetch(1)[0].json_data
    return val


class AutoVivification(dict):
    """Implementation of perl's autovivification feature."""
    def __getitem__(self, item):
        try:
            return dict.__getitem__(self, item)
        except KeyError:
            value = self[item] = type(self)()
            return value


def post_processor(filename, epoch=False, Date=False):

    f = getting_json(filename)
    content = json.loads(f)
    date = []
    time_tuple_list = []
    master = AutoVivification()
    l = []
    for k, v in content.items():
        if epoch:
            date = time.strftime("%d %m %Y", time.gmtime(float(k) / 1000.0))
            date = date.split()
            day = date[0]
            month = date[1]
            year = date[2]
            t_tuple = (day, month, year)
            if t_tuple in time_tuple_list:
                l = master[year][month][day]
            else:
                l = []
                time_tuple_list.append(t_tuple)
            print v
            if Date:
                v["Date"] = time.strftime("%d %m %Y %H:%M %Z", time.gmtime(float(v["Date"]) / 1000.0))
            l.append(v)
            master[year][month][day] = l
    print json.dumps(master)
    f = json.dumps(master)
    t = dtModel(id="done_json", name="done_" + filename, json_data=f)
    t.put()


def analytics(filename):

    cab_app = ['Uber', 'OlaCabs']
    text_app = ['WhatsApp', 'imo', 'Hangouts', 'Messaging']
    social_app = ['Twitter', 'Pinterest', 'Instagram']
    call_app = ['Dialler']
    food_app = ['foodpanda', 'TinyOwl', 'Swiggy']

    f = getting_json(filename)
    content = json.loads(f)
    year_dict = {}

    for main, year in content.items():
        month_dict = {}
        for month, calllist in year.items():
            day_dict = {}
            for day, n_calls in calllist.items():
                appinfo = {}
                appinfo['social_app'] = 0
                appinfo['cab_app'] = 0
                appinfo['text_app'] = 0
                appinfo['food_app'] = 0
                appinfo['call_app'] = 0
                for call_info in n_calls:
                    app_type = ""
                    if call_info['Name'] in social_app:
                        app_type = "social_app"
                    elif call_info['Name'] in cab_app:
                        app_type = "cab_app"
                    elif call_info["Name"] in  text_app:
                        app_type = "text_app"
                    elif call_info["Name"] in  food_app:
                        app_type = "food_app"
                    elif call_info["Name"] in  call_app:
                        app_type = "call_app"
                    if app_type != "":
                        temp = int(call_info['Foreground'])
                        appinfo[app_type] += temp
                day_dict[day] = appinfo
            month_dict[month] = day_dict
        year_dict[main] = month_dict
        y = json.dumps(year_dict)
        t = dtModel(id = "analytics__json", name="analytics_" + filename, json_data=y)
        t.put()

    print json.dumps(year_dict)


@app.route('/moredetails', methods=["POST"])
def getdetails():
    allowe_app = []
    return_list = {}
    return_list['used_app'] = []
    date = request.json
    date_split = date['date'].split("/")
    index = date['index']
    app_type = {1: "food_app", 2: "text_app", 3: "cab_app",
                4: "call_app", 5: "socail_app"}

    if app_type[index] == "food_app":
        allowe_app = ['foodpanda', 'TinyOwl', 'Swiggy']
    elif app_type[index] == "text_app":
        allowe_app = ['WhatsApp', 'imo', 'Hangouts', 'Messaging']
    elif app_type[index] == "cab_app":
        allowe_app = ['Uber', 'OlaCabs']
    elif app_type[index] == "socail_app":
        allowe_app = ['Twitter', 'Pinterest', 'Instagram']
    elif app_type[index] == "call_app":
        allowe_app = ['Dialler']
    done_json = getting_json("done_raw_app_json")
    f = json.loads(done_json)
    wanted_json = f[date_split[2]][date_split[1]][date_split[0]]
    for i in wanted_json:
        if i["Name"] in allowe_app:
            print i["Name"]
            return_list['used_app'].append(i)
            r = json.dumps(return_list)
    return r


@app.route('/')
def hello():
    """Return a friendly HTTP greeting."""
    return 'This is not where you want to be yada-yada-yada.. goto /stats to see some action :P'


@app.route("/json")
def post_json():
    f = open("json_folder/appUseageStats.json", 'r')
    f = json.loads(f.read())
    f = json.dumps(f)
    print f
    t = dtModel(id="raw_app", name="raw_app_json", json_data=f)
    ndb.Key('dtModel', 7001)
    t.put()
    post_processor("raw_app_json", True)
    analytics('done_raw_app_json')
    return 'done ;)'


@app.route('/stats')
def get_stats():
    app_json = getting_json('analytics_done_raw_app_json')
    app_json = json.loads(app_json)
    app_json = OrderedDict(sorted(app_json.items(), key=lambda t: t[0]))
    return render_template('stats.html', appinfo=app_json)


@app.errorhandler(404)
def page_not_found(e):
    """Return a custom 404 error."""
    return 'Sorry, Nothing at this URL.', 404


@app.errorhandler(500)
def application_error(e):
    """Return a custom 500 error."""
    return 'Sorry, unexpected error: {}'.format(e), 500
