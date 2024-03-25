from abc import ABC, abstractmethod
from typing import Any


class BaseAgent(ABC):
    @abstractmethod
    def interact(self, **requests: Any) -> str:
        pass


class DummyAgent(BaseAgent):
    def interact(self, **requests: Any) -> str:
        return "hi"
