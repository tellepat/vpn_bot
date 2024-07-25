#!/bin/bash

# Получение внешнего IP-адреса
EXTERNAL_IP=$(curl -s https://ifconfig.me)

# Проверка, удалось ли получить IP-адрес
if [ -z "$EXTERNAL_IP" ]; then
  echo "Не удалось получить внешний IP-адрес."
  exit 1
fi

echo "Внешний IP-адрес: $EXTERNAL_IP"

# Запуск контейнера
podman run -d \
  --name wireguard \
  --cap-add NET_ADMIN \
  --cap-add SYS_MODULE \
  -v ./config:/config \
  -v /lib/modules:/lib/modules \
  -p 51820:51820/udp \
  -p 5000:5000 \
  -e SERVER_IP=$EXTERNAL_IP \
  -e PUID=1000 \
  -e PGID=1000 \
  -e TZ=Europe/Moscow \
  --restart unless-stopped \
  localhost/api_server_wg:latest

