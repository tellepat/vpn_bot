import os


class Config:
    """
    Класс содержит конфигурацию приложения (Расположение базы sqlite, Расположение конфигурации wireguard), не менять
    без строгой необходимости
    """
    SQLALCHEMY_DATABASE_URI = 'sqlite:////config/wg.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    WG_CONFIG_PATH = '/config/wg0.conf'
