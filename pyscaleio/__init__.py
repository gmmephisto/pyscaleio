from .client import ScaleIOSession, ScaleIOClient
from .manager import ScaleIOClientsManager
from .models import (
    System, ProtectionDomain, StoragePool,
    VTree, Sdc, Volume
)

__all__ = (
    ScaleIOSession.__name__, ScaleIOClient.__name__,
    System.__name__, ProtectionDomain.__name__,
    StoragePool.__name__, VTree.__name__, Sdc.__name__,
    Volume.__name__
)

__version__ = "0.1.0"

get_client = ScaleIOClientsManager().get_client
add_client = ScaleIOClientsManager().register
