from outline_vpn.outline_vpn import OutlineVPN
from config import OUTLINE_API_URLS

def get_all_clients(location):
    config = OUTLINE_API_URLS.get(location)
    if not config:
        return []
    client = OutlineVPN(api_url=config['api_url'], cert_sha256=config['cert_sha256'])
    return client.get_keys()

def get_access_url(name, location):
    config = OUTLINE_API_URLS.get(location)
    if not config:
        return "Access denied"
    client = OutlineVPN(api_url=config['api_url'], cert_sha256=config['cert_sha256'])
    keys = client.get_keys()
    for key in keys:
        if key.name == name:
            return key.access_url
    return "Access denied"

def delete_access_url(name, location):
    config = OUTLINE_API_URLS.get(location)
    if not config:
        return "Access URL does not exist"
    client = OutlineVPN(api_url=config['api_url'], cert_sha256=config['cert_sha256'])
    keys = client.get_keys()
    for key in keys:
        if key.name == name:
            client.delete_key(key.key_id)
            return "Access URL deleted"
    return "Access URL does not exist"

def add_access_url(name, location):
    config = OUTLINE_API_URLS.get(location)
    if not config:
        return "Error creating access URL"
    client = OutlineVPN(api_url=config['api_url'], cert_sha256=config['cert_sha256'])
    new_key = client.create_key(name=name)
    return new_key.access_url
