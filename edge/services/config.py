from configparser import ConfigParser

import logging
import os

_CONFIG_PATH = "config.ini"

class Singleton(type):
    _instances = {}
    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]

class Config(metaclass=Singleton):

    def __init__(self):
        self.log = logging.getLogger(__name__)

        self.log.info("Config initialization")
        self.config = ConfigParser()
        self.config.read(_CONFIG_PATH)

        # Config.ini parse
        if not self.config.has_section("CLUSTER"):
            import uuid

            self.config.add_section("CLUSTER")
            self.config.set("CLUSTER", "id", str(uuid.uuid4()))
            self.log.info(
                f"Generated UUID for the current edge device that is {self.config.get('CLUSTER', 'id')}"
            )

        if not self.config.has_section("INFLUX_DB"):
            self.config.add_section("INFLUX_DB")
            self.config.set("INFLUX_DB", "token", "secret-token")
            self.config.set("INFLUX_DB", "org", "street-lights-iot")
            self.config.set("INFLUX_DB", "bucket", "edge1")
            self.config.set("INFLUX_DB", "server", "http://metrics-db:8086")

        if not self.config.has_section("RESOURCES_DB"):
            self.config.add_section("RESOURCES_DB")
            self.config.set("RESOURCES_DB", "name", "resources")
            self.config.set("RESOURCES_DB", "user", "street-lights-iot")
            self.config.set("RESOURCES_DB", "password", "password")
            self.config.set("RESOURCES_DB", "host", "resources-db")

        # Environment parse
        self.config.set("RESOURCES_DB","name", os.environ.get("POSTGRES_DB") or self.config.get("RESOURCES_DB", "name"))
        self.config.set("RESOURCES_DB","user", os.environ.get("POSTGRES_USER") or self.config.get("RESOURCES_DB", "user"))
        self.config.set("RESOURCES_DB","password", os.environ.get("POSTGRES_PASSWORD") or self.config.get("RESOURCES_DB", "password"))

        self.config.set("INFLUX_DB","token", os.environ.get("DOCKER_INFLUXDB_INIT_ADMIN_TOKEN") or self.config.get("INFLUX_DB", "token"))
        self.config.set("INFLUX_DB","org", os.environ.get("DOCKER_INFLUXDB_INIT_ORG") or self.config.get("INFLUX_DB", "org"))
        self.config.set("INFLUX_DB","bucket", os.environ.get("DOCKER_INFLUXDB_INIT_BUCKET") or self.config.get("INFLUX_DB", "bucket"))

        print("STO QUAAAAAAAAAA")
        print(self.config.get("RESOURCES_DB", "name"))

        with open(_CONFIG_PATH, "w") as conf:
            self.config.write(conf)

    def get_configuration(self):
        return self.config