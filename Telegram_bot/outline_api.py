from outline_vpn.outline_vpn import OutlineVPN


def get_all_clients(outline_api_url, cert_sha256):
    """
    Получение всех клиентов подключенных к серверу
    :param outline_api_url: url api сервера
    :param cert_sha256: ключ доступа к api сервера
    :return: List экземпляров класса OutlineVPN.key, содержащий всех клиентов и их параметры
    """
    client = OutlineVPN(api_url=outline_api_url, cert_sha256=cert_sha256)
    return client.get_keys()


def get_access_url(name, outline_api_url, cert_sha256):
    """
    Получение ключа доступа конкретного клиента
    :param name: Имя клиента или его chat_id
    :param outline_api_url: url api сервера
    :param cert_sha256: ключ доступа к api сервера
    :return: Ключ доступа к серверу, либо сообщает о запрете доступа
    """
    client = OutlineVPN(api_url=outline_api_url, cert_sha256=cert_sha256)
    keys = client.get_keys()
    for key in keys:
        if key.name == name:
            return key.access_url
    return "Access denied"


def delete_access_url(name, outline_api_url, cert_sha256):
    """
    Удаляет ключ доступа конкретного клиента
    :param name: Имя клиента или его chat_id
    :param outline_api_url: url api сервера
    :param cert_sha256: ключ доступа к api сервера
    :return: Булево значение успешности операции
    """
    client = OutlineVPN(api_url=outline_api_url, cert_sha256=cert_sha256)
    keys = client.get_keys()
    for key in keys:
        if key.name == name:
            client.delete_key(key.key_id)
            return True
    return False


def add_access_url(name, outline_api_url, cert_sha256):
    """
    Создаёт ключ доступа клиента на сервере
    :param name: Имя клиента или его chat_id
    :param outline_api_url: url api сервера
    :param cert_sha256: ключ доступа к api сервера
    :return: Ключ доступа клианта на сервер
    """
    client = OutlineVPN(api_url=outline_api_url, cert_sha256=cert_sha256)
    new_key = client.create_key(name=name)
    return new_key.access_url
