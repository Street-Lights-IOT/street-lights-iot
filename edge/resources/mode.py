from aiocoap.resource import Resource, Site

from resources.models import Mode
from playhouse.shortcuts import model_to_dict, dict_to_model

import aiocoap
import json


class ModeResource(Resource):
    """Resource that represents the current enabled mode for the cluster"""

    def __init__(self, mode: Mode):
        super().__init__()
        self._mode = mode

    @classmethod
    def from_data(cls, data: Mode):
        return cls(
            data.lamps_after,
            data.illumination_duration_seconds,
            data.enabled,
        )

    async def render_get(self, request):
        mode = self.to_dict()
        min = [r["min"] for r in mode["ranges"]]
        wm = [r["with_movement"] for r in mode["ranges"]]
        wom = [r["without_movement"] for r in mode["ranges"]]

        payload = {
            "la": mode["lamps_after"],
            "is": mode["illumination_duration_seconds"],
            "min": min,
            "wm": wm,
            "wom": wom,
        }

        return aiocoap.Message(
            payload=json.dumps(payload).encode("utf-8"), token=request.token,
        )

    def to_json(self):
        return json.dumps(self.to_dict())

    def to_dict(self):
        temp = model_to_dict(self._mode)

        temp["ranges"] = list()
        for r in self._mode.ranges.dicts():
            temp["ranges"].append(r)

        return temp
