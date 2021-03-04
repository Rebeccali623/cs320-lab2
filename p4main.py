# project: p4
# submitter: hli623
# partner: none

# source of data:https://www.kaggle.com/terenceshin/covid19s-impact-on-airport-traffic?select=covid_impact_on_airport_traffic.csv
# I choosed some citys in Canada. From this data, I can know how does the covid impact the airpot in different citys in Canada. I can draw a line graph that has date on the x-axis and percentofbaseline on the y-axis.

import pandas as pd
from flask import Flask, request, jsonify
import re
import requests

app = Flask(__name__)
df = pd.read_csv("main.csv")
red = 0
blue = 0
cnt = 0
n = 0

@app.route('/')
def home():
    global cnt
    global red
    global blue
    cnt += 1
    with open("index.html") as f:
        html = f.read()
    if cnt <= 10:
        if cnt%2 == 0:
            html = html.replace("#FF0000","#0000FF")
            html = html.replace("?from=A","?from=B")
    else:
        if blue >= red:
            html = html.replace("#FF0000","#0000FF")
            html = html.replace("?from=A","?from=B")
    return html

@app.route('/browse.html')
def browse_page():
    return "<html><body><h1>{}</h1><p>{}</p></body></html>".format("Browse",df.to_html())

@app.route('/email', methods=["POST"])
def email():
    global n
    email = str(request.data, "utf-8")
    if re.match(r"^[A-Za-z0-9\.\+_-]+@[A-Za-z0-9\._-]+\.[a-zA-Z]*$", email): # 1
        with open("emails.txt", "a") as f: # open file in append mode
                f.write(email + "\n") # 2
                n += 1
        return jsonify("thanks, you're subscriber number {}!".format(n))
    return jsonify("Invalid email address.") # 3

@app.route('/donate.html')
def donate_page():
    global red
    global blue
    if request.args.get("from") == "A":
        red += 1
    if request.args.get("from") == "B":
        blue += 1
    return "<html><body><h1>{}</h1><p>{}</p></body></html>".format("Donations","Please!")

@app.route('/api.html')
def api_page():
    with open("api.html") as f:
        html = f.read()
    return html

@app.route('/maincols.json')
def maincols():
    return jsonify(Date=str(df.Date.dtype),
                   PercentOfBaseline=str(df.PercentOfBaseline.dtype),
                   City=str(df.City.dtype))

@app.route('/main.json')
def main():
    ls = []
    for i in range(len(df)):
        dic = dict(df.iloc[i])
        dic['Date'] = str(dic['Date'])
        dic['PercentOfBaseline'] = int(dic['PercentOfBaseline'])
        dic['City'] = str(dic['City'])
        ls.append(dic)
    if request.args.get("min_PercentOfBaseline") == "50":
        copy = []
        for i in range(len(ls)):
            if int(ls[i]['PercentOfBaseline'])>=50:
                copy.append([i,ls[i]])
        ls = copy
    return jsonify(ls)
    
    
    
if __name__ == '__main__':
    app.run(host="0.0.0.0") # don't change this line!
    
    
    
    
   