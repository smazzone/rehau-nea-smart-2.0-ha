"""The rehau_nea_smart_2 component mqttclient."""

from .Controller import Controller
from .MqttClient import MqttClient
from .models import (
    Cooling,
    Heating,
    Setpoints,
    Channel,
    Zone,
    Group,
    Installation,
)
from .utils import EnergyLevels, OperationModes
from .exceptions import (
    MqttClientError,
    MqttClientAuthenticationError,
    MqttClientCommunicationError,
)

_LOGGER = logging.getLogger(__name__)

def __init__():
    """Initialize the rehau_nea_smart_2 component mqttclient."""
    _LOGGER.debug("Initializing NEA SMART 2 HACS INTEGRATION")
    pass
