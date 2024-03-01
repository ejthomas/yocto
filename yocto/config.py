class Config:
    SECRET_KEY = "dev"  # default if not overwritten from file in __init__
    DEBUG = False

class DevelopmentConfig(Config):
    DEBUG = True
    DATABASE = "dev"

class ProductionConfig(Config):
    DEBUG = False
    DATABASE = "yocto"

class TestingConfig(Config):
    DEBUG = True
    TESTING = True
    DATABASE = "tests"
