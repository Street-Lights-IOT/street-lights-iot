from services.database import Database
from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS
from datetime import datetime

import peewee as pw

class BaseModel(pw.Model):
    class Meta:
        database = Database().get_db()

class StreetLight(BaseModel):
    """Model that represents the street light"""
    mac = pw.CharField()
    order = pw.IntegerField()
    ip = pw.CharField()
    registered_at = pw.DateTimeField(default=datetime.utcnow, null=True)
    last_seen_at = pw.DateTimeField(default=datetime.utcnow, null=True)
    # self.registered_at = registered_at if registered_at else datetime.utcnow().replace(microsecond=0).isoformat()
    # self.last_seen_at = last_seen_at if last_seen_at else datetime.utcnow().replace(microsecond=0).isoformat()

class Mode(BaseModel):
    """Model that represents the mode"""
    lamps_after = pw.SmallIntegerField(default=2)
    illumination_duration_seconds = pw.SmallIntegerField(default=10)
    enabled = pw.BooleanField(default=False)

    # mode: {lamps_after, illum_duration, ranges:{min, with_mov, no_mov}}
    # {la:2, is:20, min: [0, 200,300, 400, 500], wm:[50, 30, 30, 30, 60], wom:[50, 30, 30, 30, 60]}

class Range(BaseModel):
    """Model that represents the range"""
    min = pw.IntegerField()
    with_movement = pw.SmallIntegerField() # percentage
    without_movement = pw.SmallIntegerField() # percentage
    mode = pw.ForeignKeyField(Mode, backref="ranges", lazy_load=False)