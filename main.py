from datetime import datetime
from bson.objectid import ObjectId
from flask import Flask, app
from flask_restful import Api, Resource, reqparse
import pymongo
from bson import json_util
import json
from flask_cors import CORS
from pytz import timezone
import pytz

client = pymongo.MongoClient("mongodb+srv://iotUser:yS86a99GnCVg3jCt@cluster0.hgxbh.mongodb.net/myFirstDatabase?retryWrites=true&w=majority")

db = client["ioTTelemetry"]
sensors_collection = db["Sensors"]
readouts_collection = db["Readouts"]

app = Flask(__name__)
CORS(app)
api = Api(app)


def parse_json(data):
    return json.loads(json_util.dumps(data))


class Sensors(Resource):
    def get(self):
        sensor_data = sensors_collection.find()
        data_list = []
        for data in sensor_data:
            data["_id"] = str(data["_id"])
            data_list.append(data)
        return data_list, 200

    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument("location", required=True)
        parser.add_argument("reading")
        parser.add_argument("humidity")
        args = parser.parse_args()
        sensors_collection.insert_one(args)
        return 201


class Sensor(Resource):
    def get(self, id):
        sensor_data = sensors_collection.find_one({"_id": ObjectId(id)})
        if sensor_data == None:
            return None, 404
        sensor_data["_id"] = str(sensor_data["_id"])
        return sensor_data, 201

    def post(self, id):
        parser = reqparse.RequestParser()
        parser.add_argument("location", required=True)
        parser.add_argument("reading")
        args = parser.parse_args()
        args["_id"] = ObjectId(id)

        sensors_collection.insert_one(args)
        return args, 201

    def put(self, id):
        sensor_data = sensors_collection.find_one({"_id": ObjectId(id)})
        if sensor_data == None:
            return None, 404
        parser = reqparse.RequestParser()
        parser.add_argument("location", required=True)
        parser.add_argument("type", required=True)
        args = parser.parse_args()

        sensors_collection.find_one_and_update({"_id": ObjectId(id)},
                                               {"$set": {"location": args["location"],
                                                         "type": args["type"]}})

    def delete(self, id):
        sensors_collection.delete_one({"_id": ObjectId(id)})
        return "", 204


class Readouts(Resource):
    def get(self):
        readout_data = readouts_collection.find()
        data_list = []
        for data in readout_data:
            data["_id"] = str(data["_id"])
            data_list.append(data)
        return data_list, 200

    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument("sensor_id", required=True)
        parser.add_argument("value", required=True)
        parser.add_argument("humidity", required=True)
        args = parser.parse_args()
        date_object = datetime.now(tz=pytz.utc)
        date_object = date_object.astimezone(timezone('US/Pacific'))
        args["date"] = date_object.strftime("%x")

        hour = date_object.strftime("%I")
        minute = date_object.strftime("%M")
        am_pm = date_object.strftime("%p")

        final_time = hour + ":" + minute + " " + am_pm
        args["time"] = final_time

        readouts_collection.insert_one(args)

        #Update sensor
        sensor_data = sensors_collection.find_one_and_update({"_id": ObjectId(args["sensor_id"])},
                                                             {"$set": {"reading": args["value"]}})

        sensor_data = sensors_collection.find_one_and_update({"_id": ObjectId(args["sensor_id"])},
                                                             {"$set": {"humidity": args["humidity"]}})

        return 201

    def delete(self):
        readouts_collection.delete_many({})
        return 201


class SensorReadouts(Resource):
    def get(self, id):
        readout_list = []
        readouts = readouts_collection.find()
        for readout in readouts:
            readout["_id"] = str(readout["_id"])
            if readout["sensor_id"] == id:
                readout_list.append(readout)
        return readout_list, 200


class Recents(Resource):
    def get(self):
        readout_list = []
        readouts = readouts_collection.find().sort("_id", -1).limit(50)

        for readout in readouts:
            readout["_id"] = str(readout["_id"])
            readout_list.append(readout)
        return readout_list, 200


class JSONEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, ObjectId):
            return str(o)
        return json.JSONEncoder.default(self, o)


api.add_resource(Sensors, "/sensors")
api.add_resource(Sensor, "/sensor/<string:id>")
api.add_resource(Readouts, "/readouts")
api.add_resource(SensorReadouts, "/sensor/<string:id>/readouts")
api.add_resource(Recents, "/readouts/recents")

if __name__ == "__main__":
	app.run(host="0.0.0.0", port=5000)
