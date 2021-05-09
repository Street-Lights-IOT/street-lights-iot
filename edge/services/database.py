from services.config import Config
from peewee import PostgresqlDatabase
from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS
from datetime import datetime

import logging


class Database(object):
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Database, cls).__new__(cls)
            cls._init(cls)

        return cls._instance

    def _init(cls):
        cls.log = logging.getLogger(__name__)
        cls.log.info("Initializing databases")
        config = Config().get_configuration()

        cls.db = PostgresqlDatabase(config.get("RESOURCES_DB", "name"), user=config.get("RESOURCES_DB", "user"), password=config.get("RESOURCES_DB", "password"), host=config.get("RESOURCES_DB", "host"))

        cls._influx_token = config.get("INFLUX_DB", "token")
        cls.influx_org = config.get("INFLUX_DB", "org")
        cls.influx_bucket = config.get("INFLUX_DB", "bucket")
        cls.influx_client = InfluxDBClient(
            url=config.get("INFLUX_DB", "server"), token=cls._influx_token
        )
        cls.influx_write_api = cls.influx_client.write_api(write_options=SYNCHRONOUS)

    def get_db(cls):
        return cls.db

    def influx_write_brightness(cls, order, value, time=datetime.utcnow()):
        point = Point("brightness").tag("street-light", order).field("percent" ,value).time(time, WritePrecision.S)
        cls.influx_write_api.write(cls.influx_bucket, cls.influx_org, point)

    def influx_write_proximity(cls, order, value, time=datetime.utcnow()):
        point = Point("proximity").tag("street-light", order).field("value" ,value).time(time, WritePrecision.S)
        cls.influx_write_api.write(cls.influx_bucket, cls.influx_org, point)