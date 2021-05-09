import re

def get_ip_from_socket_address(socket_address):
    return re.sub(":\d*$", "", socket_address)