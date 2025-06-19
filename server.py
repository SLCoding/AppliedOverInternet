from influxdb_client import Point, InfluxDBClient, WriteApi
import traceback
import os
import json
from pathlib import Path
from dotenv import load_dotenv
from datetime import datetime, timezone

from flask import *

load_dotenv()
app = Flask(__name__)

# https://stackoverflow.com/a/37331139
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 60*60*24*30 # 30 days

DATA = None
LAST_UPDATE = None

def initDBClient() -> InfluxDBClient:
    if not os.getenv("DB_HOST"):
        raise Exception("DB_HOST not set in .env")
    
    db_client = InfluxDBClient(
        url=os.getenv("DB_HOST"),
        token=os.getenv("DB_TOKEN"),
        org="test")
    if not db_client.ping():
        raise Exception("Connection failed for unknown reason")
    return db_client

def processAe2Payload(data):
    points = []

    for item in data["items"]:
        # what about nbt data. check tech reborn storages. 
        points.append(Point("ae2_item")
            .tag("name", item["technicalName"])
            .tag("type", "item")
            .field("amount", float(item["count"])))
    for fluid in data["fluids"]:
        points.append(Point("ae2_item")
            .tag("name", fluid["name"])
            .tag("type", "fluid")
            .field("amount", float(fluid["amount"]/1000)))
        
    return points

db_client = None
db_client_write_api = None
try:
    db_client = initDBClient()
    db_client_write_api = db_client.write_api()
    print("DB client connnected successfully")
except Exception as e:
    print(f"Failed to init DB client:")
    print(traceback.format_exc())
    print("data will not be sent to DB, you will not be able to use Grafana")

# For debugging purposes
@app.route('/ae2', methods=["GET"])
def ae2_get():
    return jsonify(DATA), 200

# Used by the CC:Tweaked script
@app.route('/ae2', methods=["POST"])
def ae2_post():
    if request.headers.get("X-API-KEY") != os.environ.get("API_KEY"):
        return 'Unauthorized', 403
    
    DATA = request.json
    
    db_client_write_api.write("test", "test", processAe2Payload(request.json))
    return '', 200

if __name__ == '__main__':
    print("Starting web server")
    app.run(host='0.0.0.0')
