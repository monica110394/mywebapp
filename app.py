from flask import Flask, render_template, request
from flask import jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime as dt
import secrets
import pymysql
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


app = Flask(__name__)

@app.route('/')
def index():
    locations = create_locations_makers()
    return render_template('index.html', ACCESS_KEY=MAPBOX_ACCESS_KEY, locations=locations)

MAPBOX_ACCESS_KEY = 'pk.eyJ1Ijoid2VpbSIsImEiOiJja2Ewd3VzbDUwNmc2M2ZwZDV6N3pwdmhvIn0.EJHXebn_BEqc2lzZU6KrRQ'

connection = mysql.connector.connect(host='scrubshrub.ciu4ws9ihfad.ap-southeast-2.rds.amazonaws.com',
                                         database='scrubshrub', user='Scrubshrub', password='sse1881ess')
sql_select_Query = "SELECT latitude, longitude FROM scrubshrub.test WHERE isArrowhead=1"
cursor = connection.cursor()
cursor.execute(sql_select_Query)
records = cursor.fetchall()
print("Total number of rows in test is: ", cursor.rowcount)
# tuple: (lat, lng)

def get_route_image():
    ROUTE = []
    for row in list(set(records)):
        dic = {}
        dic["lat"] = float(row[0])
        dic["long"] = float(row[1])
        ROUTE.append(dic)
        return ROUTE

# Mapbox driving direction API call
ROUTE_URL = "https://api.mapbox.com/directions/v5/mapbox/driving/{0}.json?access_token={1}&overview=full&geometries=geojson"


def create_locations_makers():
    locations = []
    ROUTE = get_route_image()
    for i in ROUTE:
        point = Point([i['long'], i['lat']])
        properties = {
            'icon': 'campsite'
            # 'marker-color': '#3bb2d0'
        }
        feature = Feature(geometry=point, properties=properties)
        locations.append(feature)
    print(locations)
    return locations

# def get_model():
#     global model
#     model=tensorflow.keras.models.load_model('model_1_2.h5')
#     model=load_model('model_1_2.h5')
#     print(" * Model loaded!")
    
def preprocess_image(image, target_size):
    if image.mode != "RGB":
        image=image.convert("RGB")
    image=image.resize(target_size)
    image=img_to_array(image)
    image=np.expand_dims(image, axis=0)
    return image

@app.route("/predict",methods=['POST'])
def predict(): 
    global file, pred_neg, pred_arr
    message=request.get_json(force=True)
    encoded=message['image']
    decoded=base64.b64decode(encoded) 
    image=Image.open(io.BytesIO(decoded))
    file = decoded
    processed_image=preprocess_image(image, target_size=(224,224))
    global model
    model=tf.keras.models.load_model('model_1_2.h5', compile=False)
    prediction = model.predict(processed_image).tolist()
    pred_neg = prediction[0][0]
    pred_arr = prediction[0][1]
    upload()
    response = {
        'negative':pred_neg,
        'arrowhead':pred_arr
        } 
    print("\nPrediction:",response,"\n")
    if pred_arr>pred_neg:
        return jsonify({"isArrowhead":True,"message":"Congratulations! You have identified an Arrowhead. We have submitted your response successfully."})
    else:
        return jsonify({"isArrowhead":False,"message":"Sorry! It is not identified as an Arrowhead. Thank you for participating!"})

class DBConfig(object):
    DIALECT = 'mysql'
    DRIVER = 'mysqldb'
    USERNAME = 'Scrubshrub'
    PASSWORD = 'sse1881ess'
    HOST = 'scrubshrub.ciu4ws9ihfad.ap-southeast-2.rds.amazonaws.com'
    PORT = '3306'
    DATABASE = 'scrubshrub'
    app.config['SQLALCHEMY_DATABASE_URI'] = "{}+{}://{}:{}@{}:{}/{}?charset=utf8".format(DIALECT, DRIVER,
                                                                                                 USERNAME, PASSWORD,
                                                                                                 HOST, PORT, DATABASE)
    SQLALCHEMY_TRACK_MODIFICATIONS = True


app.config.from_object(DBConfig)

db = SQLAlchemy(app)


class SS(db.Model):
    global lat, lng
    __tablename__="test"
    id = db.Column(db.String(20), primary_key=True)
    data = db.Column(db.LargeBinary, nullable=False)
    latitude = db.Column(db.Float(300), nullable=True)
    longitude = db.Column(db.Float(300), nullable=True)
    date_time = db.Column(db.DateTime(), nullable=False)
    isNegative = db.Column(db.Integer(), nullable=False)
    isArrowhead = db.Column(db.Integer(), nullable=False)


@app.route('/location', methods=['POST','GET'])
def location():
    global lat, lng
    data = request.get_json()
    coords=data['location']
    lat=coords['lat']
    lng=coords['lng']
    print('Latitude:', lat)
    print('Longiude:', lng)
    return jsonify(data)


@app.route('/upload')
def upload():
    global i_d
    i_d = secrets.token_hex(16)
    role1 = SS(id=i_d, data=file, latitude=lat, longitude=lng, isNegative=pred_neg, isArrowhead=pred_arr, date_time=dt.now())
    db.session.add(role1)
    db.session.commit()
    return jsonify(i_d)

if __name__ == "__main__":
    app.run()

    
    


