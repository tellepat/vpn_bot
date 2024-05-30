#!/bin/bash

# Initialize database
/app/venv/bin/python /app/db.py init

# Проверка существования ключей сервера
if [ ! -f /config/server_private_key ] || [ ! -f /config/server_public_key ]; then
    # Генерация ключей сервера
    SERVER_PRIVATE_KEY=$(wg genkey)
    SERVER_PUBLIC_KEY=$(echo $SERVER_PRIVATE_KEY | wg pubkey)

    # Сохранение ключей в файлы
    echo $SERVER_PRIVATE_KEY > /config/server_private_key
    echo $SERVER_PUBLIC_KEY > /config/server_public_key
else
    # Чтение ключей из файлов
    SERVER_PRIVATE_KEY=$(cat /config/server_private_key)
    SERVER_PUBLIC_KEY=$(cat /config/server_public_key)
fi

# Создание серверного конфигурационного файла
cat <<EOL > /config/wg0.conf
[Interface]
PrivateKey = $SERVER_PRIVATE_KEY
Address = 10.0.0.1/24
ListenPort = 51820
EOL

# Создание символической ссылки
mkdir -p /etc/wireguard
ln -s /config/wg0.conf /etc/wireguard/wg0.conf

# Enable IP forwarding
sysctl -w net.ipv4.ip_forward=1

# Setup masquerading
iptables -t nat -A POSTROUTING -o eth0 -j MASQUERADE

# Start WireGuard
wg-quick up wg0

# Запуск Flask API
/app/venv/bin/python /app/app.py &

# Keep the container running
tail -f /dev/null
