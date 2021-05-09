from services.database import Database
from resources.models import Range, Mode, StreetLight

db = Database().db
db.connect()
db.create_tables([StreetLight, Mode, Range])

# Insert modes
mode = Mode(lamps_after=3, illumination_duration_seconds=10, proximity_refresh=5, brigthness_refresh=5, enabled=False)
mode.save()

mode = Mode(lamps_after=2, illumination_duration_seconds=10, proximity_refresh=60, brigthness_refresh=60, enabled=True)
mode.save()

# Insert ranges
ranges = [{"min":20, "with_movement":70, "without_movement":10}, {"min":40, "with_movement":80, "without_movement": 20}, {"min":40, "with_movement":80, "without_movement": 20}, {"min":40, "with_movement":80, "without_movement": 20}, {"min":40, "with_movement":80, "without_movement": 20}]
for range in ranges:
    new_range = Range(min=range.get("min"), with_movement=range.get("with_movement"), without_movement=range.get("without_movement"), mode=mode)
    print("Range added: " + str(new_range.save() > 0))

mode = Mode.get_or_none(Mode.enabled == True)

for r in mode.ranges:
    print(r.__data__)

db.close()