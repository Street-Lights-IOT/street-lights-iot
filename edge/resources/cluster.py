from aiocoap.resource import Resource, Site
from resources.streetlight import StreetLightResource
from resources.mode import ModeResource
from peewee import *
from playhouse.shortcuts import model_to_dict, dict_to_model
from resources.models import StreetLight, Mode, Range
from datetime import datetime

import logging
import aiocoap
import utils
import json

from services.database import Database


class ClusterResource(Resource):
    def __init__(self, cluster):
        super().__init__()
        self.cluster = cluster
        self.lights = []
        self.lamps_after = 2
        self.illumination_duration = 4
        self.ranges = []
        self.mode = None

        # mode: {lamps_after, illum_duration, ranges:{min, with_mov, no_mov}}
        # {la:2, is:20, min: [0, 200,300, 400, 500], wm:[50, 30, 30, 30, 60], wom:[50, 30, 30, 30, 60]}

        # Read from lights stored in the database
        for light in StreetLight.select():
            registered_light = StreetLightResource.from_light_data(light)
            self.lights.append(registered_light)

        # Read enabled mode
        enabledMode = Mode.get_or_none(Mode.enabled == True)
        if enabledMode:
            self.mode = ModeResource(enabledMode)

    def find_subsequents(self, k, ip):
        # Under the assumption that the list is always ordered!

        index = -1
        for index, light in enumerate(self.lights):
            if light.ip == ip:
                return self.lights[index + 1 : index + 1 + k]

        return []

    async def render_get(self, request):
        lights = [
            l.to_dict()
            for l in self.find_subsequents(
                2, utils.get_ip_from_socket_address(request.remote.hostinfo)
            )
        ]

        payload = []
        for l in lights:
            print("order: " + str(l.get("order")))
            payload.append(l.get("ip").split(".")) # [[192,168,20,70], [192,50,30,20]]

        return aiocoap.Message(
            payload=json.dumps(payload).encode("utf-8"), token=request.token
        )

    async def render_post(self, request):
        """Add a new street light to the cluster
        """

        data = json.loads(request.payload)
        new_light = StreetLightResource(
            data["mac"],
            len(self.lights) + 1,
            utils.get_ip_from_socket_address(request.remote.hostinfo),
            registered_at=datetime.utcnow().isoformat(),
            last_seen_at=datetime.utcnow().isoformat()
        )
        print("NEW LIGHT CI PROVA")

        # Search if MAC is already registered
        found = False
        for light in self.lights:
            if light.mac == new_light.mac:
                found = True
                print("MAC UGUALE")
                if light.ip != new_light.ip:
                    light.ip = new_light.ip
                    print("IP UGUALE")
                    light.seen()
                    light.save()
                
                payload = json.dumps({"order": light.order})

                return aiocoap.Message(
                    code=aiocoap.Code.CHANGED,
                    payload=payload.encode("utf-8"),
                    token=request.token,
                )

        if not found:
            print("NULLA TROVAI")
            self.lights.append(new_light)
            self.cluster.add_light_resource(new_light)
            saved = new_light.save()

            if saved:
                logging.info(
                    f"The IP address {utils.get_ip_from_socket_address(request.remote.hostinfo)} just registered"
                )

                payload = json.dumps({"order": self.lights[-1].order})

                return aiocoap.Message(
                    code=aiocoap.Code.CREATED,
                    payload=payload.encode("utf-8"),
                    token=request.token,
                )

        return aiocoap.Message(
            code=aiocoap.Code.INTERNAL_SERVER_ERROR,
            payload=json.dumps({"error": "Server error"}).encode("utf-8"),
            token=request.token,
        )


class ClusterSite(Site):
    def __init__(self):
        super().__init__()
        self.cluster = ClusterResource(self)

        for light in self.cluster.lights:
            self.add_resource([str(light.order)], light)

        self.add_resource([], self.cluster)
        self.add_resource(["mode"], self.cluster.mode)

    def add_light_resource(self, light):
        self.add_resource([str(light.order)], light)

    def get_link_description(self):
        # Publish additional data for the Cluster resource, ct=51 is application/json
        return dict(
            **super().get_link_description(),
            title=f"The cluster of street lightings managed by this edge",
            ct="51",
        )
