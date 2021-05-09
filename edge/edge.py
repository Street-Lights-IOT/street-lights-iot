import logging
import logging.config
import asyncio
import aiocoap

def init_config(logger):
    from services.config import Config
    config = Config().get_configuration()
    logger.info("Cluster ID: " + config.get("CLUSTER", "id"))

def init_resource_tree():
    from resources.cluster import ClusterSite
    from aiocoap.resource import Site, WKCResource

    
    root = Site()
    root.add_resource(
        [".well-known", "core"], WKCResource(root.get_resources_as_linkheader)
    )

    cluster = ClusterSite()
    root.add_resource(["lights"], cluster)

    return root

def init_resource_database():
    from services.database import Database
    from resources.models import StreetLight, Mode, Range

    db = Database().db
    db.connect()
    db.create_tables([StreetLight, Mode, Range])

def init_influx_database():
    pass


def main():
    # Init logger
    logging.config.fileConfig('logging.conf')
    logging.getLogger("coap-server").setLevel(logging.DEBUG)    # TODO move this in the configuration
    logger = logging.getLogger(__name__)

    # Initialization
    init_config(logger)
    init_resource_database()
    root = init_resource_tree()

    # Start the server
    asyncio.Task(aiocoap.Context.create_server_context(root))
    asyncio.get_event_loop().run_forever()


if __name__ == "__main__":
    main()
