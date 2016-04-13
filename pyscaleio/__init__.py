from .client import ScaleIOSession, ScaleIOClient
from .manager import ScaleIOClientsManager

__all__ = (
    ScaleIOSession.__name__,
    ScaleIOClient.__name__,
)

__version__ = "0.0.1"

get_client = ScaleIOClientsManager().get_client
add_client = ScaleIOClientsManager().register
