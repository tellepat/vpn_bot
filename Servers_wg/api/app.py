from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
import subprocess
import os
import re
from config import Config

app = Flask(__name__)
app.config.from_object(Config)
db = SQLAlchemy(app)

class Client(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=True, nullable=False)
    private_key = db.Column(db.String(255), nullable=False)
    public_key = db.Column(db.String(255), nullable=False)
    ip_address = db.Column(db.String(15), nullable=False)

    def __repr__(self):
        return f'<Client {self.name}>'

class ServerConfig(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    private_key = db.Column(db.String(255), nullable=False)
    public_key = db.Column(db.String(255), nullable=False)

    def __repr__(self):
        return f'<ServerConfig>'

def get_server_keys():
    config = ServerConfig.query.first()
    if config is None:
        with open('/config/server_private_key', 'r') as f:
            private_key = f.read().strip()
        with open('/config/server_public_key', 'r') as f:
            public_key = f.read().strip()
        config = ServerConfig(private_key=private_key, public_key=public_key)
        db.session.add(config)
        db.session.commit()
    return config.private_key, config.public_key

@app.route('/add_client', methods=['POST'])
def add_client():
    client_name = request.json.get('name')
    if not client_name:
        return jsonify({"error": "Client name is required"}), 400

    private_key = subprocess.check_output(['wg', 'genkey']).strip().decode('utf-8')
    public_key = subprocess.check_output(['wg', 'pubkey'], input=private_key.encode()).strip().decode('utf-8')
    ip_address = f"10.0.0.{Client.query.count() + 2}/24"  # Assuming server uses 10.0.0.1

    new_client = Client(name=client_name, private_key=private_key, public_key=public_key, ip_address=ip_address)
    db.session.add(new_client)
    db.session.commit()

    client_config = generate_client_config(private_key, ip_address)

    with open(app.config['WG_CONFIG_PATH'], 'a') as wg_conf:
        wg_conf.write(f"\n[Peer]\nPublicKey = {public_key}\nAllowedIPs = {ip_address}\n")

    restart_wireguard()

    return jsonify({"client_config": client_config}), 201

@app.route('/remove_client', methods=['POST'])
def remove_client():
    client_name = request.json.get('name')
    if not client_name:
        return jsonify({"error": "Client name is required"}), 400

    client = Client.query.filter_by(name=client_name).first()
    if not client:
        return jsonify({"error": "Client not found"}), 404

    db.session.delete(client)
    db.session.commit()

    update_server_config()
    restart_wireguard()

    return jsonify({"status": "Client removed"}), 200

@app.route('/clients', methods=['GET'])
def list_clients():
    clients = Client.query.all()
    return jsonify([{"name": client.name, "public_key": client.public_key, "ip_address": client.ip_address} for client in clients])

def generate_client_config(private_key, ip_address):
    server_private_key, server_public_key = get_server_keys()
    server_ip = os.environ.get('SERVER_IP', '127.0.0.1')

    return f"""
[Interface]
PrivateKey = {private_key}
Address = {ip_address}
DNS = 8.8.8.8

[Peer]
PublicKey = {server_public_key}
Endpoint = {server_ip}:51820
AllowedIPs = 0.0.0.0/0
PersistentKeepalive = 21
"""

def update_server_config():
    server_private_key, server_public_key = get_server_keys()
    clients = Client.query.all()
    with open(app.config['WG_CONFIG_PATH'], 'w') as wg_conf:
        wg_conf.write(f"""
[Interface]
PrivateKey = {server_private_key}
Address = 10.0.0.1/24
ListenPort = 51820
""")
        for client in clients:
            wg_conf.write(f"\n[Peer]\nPublicKey = {client.public_key}\nAllowedIPs = {client.ip_address}\n")

def restart_wireguard():
    subprocess.run(['wg-quick', 'down', 'wg0'], check=True)
    subprocess.run(['wg-quick', 'up', 'wg0'], check=True)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
