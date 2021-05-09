from aiocoap.resource import Resource
from peewee import *
from playhouse.shortcuts import model_to_dict, dict_to_model
from resources.models import StreetLight
from datetime import datetime
from services.database import Database

import aiocoap
import json


class StreetLightResource(Resource):
    """Resource that represents the street light"""
    
    def __init__(self, mac, order, ip, registered_at=None, last_seen_at=None):
        super().__init__()
        self._light = StreetLight(mac=mac, order=order, ip=ip, registered_at=registered_at, last_seen_at=last_seen_at)

    @classmethod
    def from_light_data(cls, light_data):
        return cls(light_data.mac, light_data.order, light_data.ip, light_data.registered_at, light_data.last_seen_at)

    async def render_get(self, request):
        return aiocoap.Message(payload=self.to_json().encode("utf-8"), token=request.token, code=aiocoap.Code.CONTENT)

    async def render_put(self, request):
        data = json.loads(request.payload)\
        # TODO check if ip it's the same
        changed = True

        if data.get("brightness"):
            Database().influx_write_brightness(self._light.order, data.get("brightness"), datetime.utcnow())

        if data.get("proximity"):
            Database().influx_write_proximity(self._light.order, data.get("proximity"), datetime.utcnow())
        
        self.seen()

        return aiocoap.Message(code=aiocoap.CHANGED, token=request.token)

    def seen(self):
        self._light.last_seen_at = datetime.utcnow()
        self._light.save()

    def to_json(self):
        return json.dumps(self.to_dict())

    def to_dict(self):
        return model_to_dict(self._light)
        # return {"id": self.id, "registered_at": self.registered_at, "last_seen_at": self.last_seen_at, "order": self.order, "ip": self.ip, "metrics": self.metrics}

    def get_link_description(self):
        # Publish additional data for the Light resource, ct=51 is application/json
        return dict(
            **super().get_link_description(),
            title=f"The light with ID: {self.mac}, IP: {self.ip}"
        )

    def save(self):
        # It returns the number of rows changed
        return self._light.save() > 0

    # Getters / Setters
    @property
    def mac(self):
        return self._light.mac

    @property
    def order(self):
        return self._light.order

    @property
    def ip(self):
        return self._light.ip

    @mac.setter
    def mac(self, mac):
        self._light.mac = mac
        self._light.save()

    @order.setter
    def order(self, order):
        self._light.order = order
        self._light.save()

    @ip.setter
    def ip(self, ip):
        self._light.ip = ip
        self._light.save()