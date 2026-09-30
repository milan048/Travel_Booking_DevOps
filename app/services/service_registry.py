import logging

# Set up logging for services
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler()
formatter = logging.Formatter(
    '%(asctime)s %(levelname)s %(name)s : %(message)s'
)
handler.setFormatter(formatter)
if not logger.handlers:
    logger.addHandler(handler)

# Service registry dictionary
service_registry = {}

def register_service(cls):
    """
    Decorator to register a service class in the service_registry.
    """
    service_registry[cls.__name__] = cls
    return cls
