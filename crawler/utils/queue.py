from collections import deque
from dataclasses import dataclass
from enum import Enum


class Level(Enum):
    LISTING = 0
    DETAIL = 1


@dataclass(frozen=True)
class Page:
    url: str
    level: Level
    visited: bool = False


class UniqueQueue:
    def __init__(self):
        self._queue = deque()
        self._seen = set()  # Tracks elements already in the queue

    def put(self, item: Page):
        if item not in self._seen:
            self._queue.append(item)
            self._seen.add(item)
            return True  # Item was added
        return False # Item was already present

    def get(self) -> Page:
        if not self.empty():
            item = self._queue.popleft()
            self._seen.remove(item)
            return item
        raise IndexError("Queue is empty")

    def empty(self) -> bool:
        return len(self._queue) == 0

    def qsize(self) -> int:
        return len(self._queue)
