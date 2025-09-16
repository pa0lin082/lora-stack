from dotenv import dotenv_values
import sys
import os


config = {
    **dotenv_values(),  # load shared development variables
    **os.environ,  # override loaded values with environment variables
}



assert config['MQTT_HOST'] is not None, "MQTT_HOST is not set"
assert config['MQTT_PORT'] is not None, "MQTT_PORT is not set"
assert config['MQTT_USERNAME'] is not None, "MQTT_USERNAME is not set"
assert config['MQTT_PASSWORD'] is not None, "MQTT_PASSWORD is not set"
assert config['MQTT_ROOT_TOPIC'] is not None, "MQTT_ROOT_TOPIC is not set"
assert config['INFLUXDB_HOST'] is not None, "INFLUXDB_HOST is not set"
assert config['INFLUXDB_PORT'] is not None, "INFLUXDB_PORT is not set"
assert config['INFLUXDB_TOKEN'] is not None, "INFLUXDB_TOKEN is not set"
assert config['INFLUXDB_ORG'] is not None, "INFLUXDB_ORG is not set"
assert config['INFLUXDB_BUCKET'] is not None, "INFLUXDB_BUCKET is not set"


config['MQTT_PORT'] = int(config['MQTT_PORT'])




