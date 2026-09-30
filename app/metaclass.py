from sqlalchemy.orm.decl_api import DeclarativeMeta
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ServiceMeta(DeclarativeMeta):
    """
    Metaclass to ensure that all service classes implement the calculate_cost method.
    """
    def __new__(cls, name, bases, attrs):
        # Create the new class using the parent metaclass
        new_cls = super().__new__(cls, name, bases, attrs)
        is_abstract = attrs.get('__abstract__', False)
        if not is_abstract:
            # Enforce the implementation of 'calculate_cost'
            calculate_cost = getattr(new_cls, 'calculate_cost', None)
            if not calculate_cost or not callable(calculate_cost):
                error_message = f"Can't create class {name} without implementing 'calculate_cost' method"
                logger.error(error_message)
                raise TypeError(error_message)
            else:
                logger.info(f"Class {name} created successfully with 'calculate_cost' method.")
                return new_cls
