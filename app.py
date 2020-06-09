from flask import Flask, render_template, request
from flask import jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime as dt
import secrets
import pymysql
from pytz import timezone
import pytz
import tensorflow as tf
from geojson import Point, Feature
import mysql.connector

# import matplotlib.pyplot as plt
# import json
pymysql.install_as_MySQLdb()

import base64
import numpy as np
import io
from PIL import Image
# import keras
# from keras import backend as K
# from keras.models import Sequential
# from keras.models import load_model
from tensorflow.keras.preprocessing.image import img_to_array

# from keras.preprocessing.image import ImageDataGenerator
# from flask import request
# from flask import jsonify
# from flask import Flask
# import json

from google.cloud import storage

app = Flask(__name__, template_folder='templates')
app.config.from_object('config')




@app.route('/')
def index():

    global connection


    # connection = app.config['CONNECTION']
    connection = mysql.connector.connect(host=app.config['HOST'], database=app.config['DB'], user=app.config['USER'], password=app.config['PW'])
    MAPBOX_ACCESS_KEY = app.config['MAPBOX_ACCESS_KEY']


    # locations = create_locations_makers()[0]
    # latest_locatoin = create_locations_makers()[1]
    resLocations = create_locations_makers()
    locations = resLocations[0]
    latest_locatoin = resLocations[1]

    points = create_locations_points()
    return render_template('index.html', ACCESS_KEY=MAPBOX_ACCESS_KEY, locations=locations,
                           arrow_location=points, latest=latest_locatoin)





def mel_time(record_time):
    format = "%Y-%m-%d %H:%M:%S %Z%z"
    tz = pytz.timezone('UTC')
    timezone_date_time_obj = tz.localize(record_time)
    now_mel = timezone_date_time_obj.astimezone(timezone('Australia/Melbourne'))
    return now_mel.strftime(format)


def get_latest_record():
    sql_latest = 'select id, isArrowhead, date_time from scrubshrub.test where isArrowhead=1 and latitude is not null and longitude is not null order by date_time desc'
    cursor = connection.cursor(buffered=True)
    cursor.execute(sql_latest)
    latest_record = cursor.fetchone()
    cursor.close()
    print(latest_record)
    return latest_record


def get_records(query):
    cursor = connection.cursor(buffered=True)
    cursor.execute(query)
    records = cursor.fetchall()
    print("Total number of rows in test is: ", cursor.rowcount)
    cursor.close()
    return records
    # print(records)


def get_route():
    latest_record = get_latest_record()
    sql_select_Query = "SELECT latitude, longitude, id, date_time FROM scrubshrub.test WHERE isArrowhead=1 and latitude is not null and longitude is not null"
    records = get_records(sql_select_Query)
    print(records)
    # tuple: (lat, lng)
    ROUTE = []
    latest = []
    for row in list(records):
        dic = {}
        dic_latest = {}
        if row[2] == latest_record[0]:
            time = mel_time(latest_record[2])
            dic_latest['lat'] = float(row[0])
            dic_latest['long'] = float(row[1])
            dic_latest["id"] = str(row[2])
            dic_latest['time'] = time
            latest.append(dic_latest)
        else:
            time1 = mel_time(row[3])
            dic["lat"] = float(row[0])
            dic["long"] = float(row[1])
            dic["id"] = str(row[2])
            dic["time"] = time1
            ROUTE.append(dic)

    return [ROUTE, latest]


def create_locations_makers():
    locations = []
    latest_location = []
    ROUTE = get_route()[0]
    latest = get_route()[1]

    storage_client = storage.Client.from_service_account_json("nodal-alcove-277400-29e513009663.json")
    bucket = storage_client.get_bucket("nodal-alcove-277400.appspot.com")
    dlFilename = list(bucket.list_blobs(prefix=''))
    photoUrlDic = {}
    for name in dlFilename:
        blop = bucket.blob(name.name)
        photoName = str(name.name)
        photoUrlDic[photoName] = blop.public_url
        print(blop.public_url)

    for i in ROUTE:
        point = Point([i['long'], i['lat']])
        fullName = "Arrowhead/" + i['id']
        # print(fullName)
        imgLink = photoUrlDic.get(fullName, "./static/img/grass2.png")

        # imgLink = "https://storage.cloud.google.com/nodal-alcove-277400.appspot.com/Arrowhead/" + i['id'] + "?hl=zh-cn"
        # imgLink = "https://storage.cloud.google.com/nodal-alcove-277400.appspot.com/Arrowhead/" + i['id'] + "?folder=true&hl=zh-cn&organizationId=true"
        properties = {
            # 'icon': 'Users arrowhead data'
            'icon': '<img src = " ' + str(imgLink) + '" height="100px" width="100px" alt="loading"><strong><br><br>Arrowhead recognized on: </strong> <p>' + i['time'] + '</p> '
        }
        feature = Feature(geometry=point, properties=properties)
        locations.append(feature)
    if len(latest) > 0:
        j = latest[0]

        latest_point = Point([j['long'], j['lat']])

        fullName = "Arrowhead/" + j['id']
        # print(fullName)
        imgLink = photoUrlDic.get(fullName, "./static/img/grass2.png")
        # latest_properties = {'icon': j['time']}
        latest_properties = {
            'icon': '<p>' + j['time'] + '</p> <img src = " ' + str(imgLink) + '" height="100px" width="100px" alt="loading">'
            }
        latest_feature = Feature(geometry=latest_point, properties=latest_properties)
        latest_location.append(latest_feature)
    print("latest location is: ", latest_location)
    return [locations, latest_location]


def get_csv_points():
    sql_select_csv = "SELECT * FROM scrubshrub.heatmap"
    records_csv = get_records(sql_select_csv)
    # print(records_csv)
    # tuple: (lat, lng)

    locs = []
    for row in list(records_csv):
        dic2 = {}
        dic2["lat"] = float(row[1])
        dic2["long"] = float(row[2])
        locs.append(dic2)
    return locs


def create_locations_points():
    locs = get_csv_points()
    points = []
    for i in locs:
        point = Point([i['long'], i['lat']])
        properties = {

            'Description': 'Historical arrowhead data'
        }
        feature = Feature(geometry=point, properties=properties)
        points.append(feature)
    return points


# def get_model():
#     global model
#     model=tensorflow.keras.models.load_model('model_1_2.h5')
#     model=load_model('model_1_2.h5')
#     print(" * Model loaded!")

def preprocess_image(image, target_size):
    if image.mode != "RGB":
        image = image.convert("RGB")
    image = image.resize(target_size)
    image = img_to_array(image)
    image = np.expand_dims(image, axis=0)
    return image


@app.route("/predict", methods=['POST'])
def predict():
    global file, pred_neg, pred_arr
    message = request.get_json(force=True)
    encoded = message['image']
    decoded = base64.b64decode(encoded)
    image = Image.open(io.BytesIO(decoded))
    file = decoded
    processed_image = preprocess_image(image, target_size=(224, 224))
    global model
    model = tf.keras.models.load_model('model_1_2.h5', compile=False)
    prediction = model.predict(processed_image).tolist()
    pred_neg = prediction[0][0]
    pred_arr = prediction[0][1]
    upload()
    response = {
        'negative': pred_neg,
        'arrowhead': pred_arr
    }
    print("\nPrediction:", response, "\n")
    if pred_arr > pred_neg:
        return jsonify({"isArrowhead": True,
                        "message": "Congratulations! You have identified an Arrowhead. We have submitted your response successfully."})
    else:
        return jsonify({"isArrowhead": False,
                        "message": "Sorry! It is not identified as an Arrowhead. Thank you for participating!"})




db = SQLAlchemy(app)


class SS(db.Model):
    global lat, lng
    __tablename__ = "test"
    id = db.Column(db.String(20), primary_key=True)
    # data = db.Column(db.LargeBinary, nullable=True)
    latitude = db.Column(db.Float(300), nullable=True)
    longitude = db.Column(db.Float(300), nullable=True)
    date_time = db.Column(db.DateTime(), nullable=False)
    isNegative = db.Column(db.Integer(), nullable=False)
    isArrowhead = db.Column(db.Integer(), nullable=False)


@app.route('/location', methods=['POST', 'GET'])
def location():
    global lat, lng
    data = request.get_json()
    coords = data['location']
    lat = coords['lat']
    lng = coords['lng']
    print('Latitude:', lat)
    print('Longiude:', lng)
    return jsonify(data)


@app.route('/upload')
def upload():
    global i_d
    i_d = secrets.token_hex(16)

    # role1 = SS(id=i_d, data=None, latitude=lat, longitude=lng, isNegative=pred_neg, isArrowhead=pred_arr,
    #            date_time=dt.now())
    role1 = SS(id=i_d, latitude=lat, longitude=lng, isNegative=pred_neg, isArrowhead=pred_arr,
               date_time=dt.now())


    db.session.add(role1)
    db.session.commit()

    # ----------------------------------------------------------------------------
    # ----------------------------------------------------------------------------
    storage_client = storage.Client.from_service_account_json("nodal-alcove-277400-29e513009663.json")
    bucket = storage_client.get_bucket("nodal-alcove-277400.appspot.com")

    filename = "%s/%s" % ("Arrowhead", i_d)
    blob = bucket.blob(filename)

    # start_time = time.perf_counter()

    with open("uploadBuffer", "wb") as f:
        f.write(file)
    with open("uploadBuffer", 'rb') as f:
        print(f)
        blob.upload_from_file(f)

    print("Upload complete:", i_d)
    # print("Time elasped for uploading:", time.perf_counter() - start_time, "seconds")

    # ----------------------------------------------------------------------------
    # ----------------------------------------------------------------------------

    return jsonify(i_d)


if __name__ == "__main__":
    app.run(host = '127.0.0.1', port = 8080, debug = True)





