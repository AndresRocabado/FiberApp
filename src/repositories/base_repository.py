from abc import ABC, abstractmethod
from typing import Generic, List, Optional, TypeVar

T = TypeVar("T")


class BaseRepository(ABC, Generic[T]):
    @abstractmethod
    def create(self, entity: T) -> T: ...

    @abstractmethod
    def get_by_id(self, entity_id: int) -> Optional[T]: ...

    @abstractmethod
    def get_all(self) -> List[T]: ...

    @abstractmethod
    def update(self, entity: T) -> T: ...

    @abstractmethod
    def delete(self, entity_id: int) -> bool: ...
