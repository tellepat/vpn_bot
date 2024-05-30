import os

class Config:
    SQLALCHEMY_DATABASE_URI = 'sqlite:////config/wg.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    WG_CONFIG_PATH = '/config/wg0.conf'
