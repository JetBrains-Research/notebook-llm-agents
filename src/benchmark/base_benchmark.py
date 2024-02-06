from abc import ABC, abstractmethod
from typing import Any

from src.agents.agents import BaseAgent


class BaseBenchmark(ABC):
    @abstractmethod
    def evaluate(self, agent: BaseAgent, **kwargs: Any) -> float:
        pass
