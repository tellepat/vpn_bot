FROM alpine:latest

# Установка необходимых пакетов
RUN apk update
RUN apk add --no-cache wireguard-tools
RUN apk add --no-cache iptables
RUN apk add --no-cache python3
RUN apk add --no-cache py3-pip
RUN apk add --no-cache sqlite
RUN apk add --no-cache bash

# Создание рабочего каталога
WORKDIR /app

# Создание виртуального окружения и установка зависимостей
RUN python3 -m venv /app/venv
COPY api/requirements.txt /app/requirements.txt
RUN /app/venv/bin/pip install -r /app/requirements.txt

# Копирование API и скрипта инициализации
COPY api /app
COPY init.sh /init.sh
RUN chmod +x /init.sh

# Установка переменных окружения
ENV WG_CONFIG_PATH=/config/wg0.conf
ENV PATH="/app/venv/bin:$PATH"

# Expose портов
EXPOSE 51820/udp
EXPOSE 5000

# Команда запуска
CMD ["/init.sh"]
