from abc import ABC, abstractmethod
from typing import Any, Dict


class ISerializable(ABC):
    """Interface implemented by objects that can be serialized by an exporter"""

    @abstractmethod
    def to_dict(self) -> Dict[str, Any]:
        """Serialize the object to a dictionary"""
        raise NotImplementedError
