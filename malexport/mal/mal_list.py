"""
Requests MAL Lists (animelist/mangalist) for a user,
doesn't require authentication

This requests using the load_json endpoint, the same
mechanism that works on modern MAL lists
"""

import json

from typing import List
from pathlib import Path

from .list_type import ListType
from ..common import Json, safe_request_json
from ..paths import LocalDir

BASE_URL = "https://myanimelist.net/{list_type}list/{username}/load.json?status=7&order=5&offset={offset}"


OFFSET_CHUNK = 300


class MalList:
    """
    Requests/Updates the load.json endpoint for a particular user and list type
    """

    def __init__(self, list_type: ListType, localdir: LocalDir):
        self.list_type = list_type
        self.localdir = localdir

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(list_type={self.list_type}, localdir={self.localdir})"

    __str__ = __repr__

    def offset_url(self, offset: int) -> str:
        return BASE_URL.format(
            list_type=self.list_type.value,
            username=self.localdir.username,
            offset=offset,
        )

    @property
    def list_path(self) -> Path:
        return self.localdir.data_dir / f"{self.list_type.value}list.json"

    def load_list(self) -> List[Json]:
        if self.list_path.exists():
            try:
                return list(json.loads(self.list_path.read_text()))
            except json.JSONDecodeError:
                pass
        raise FileNotFoundError(f"No file found at {self.list_type.value}")

    def update_list(self) -> None:
        list_data: List[Json] = []
        # overwrite the list with new data
        offset = 0
        while True:
            url = self.offset_url(offset)
            new_data = safe_request_json(url)
            list_data.extend(new_data)
            if len(new_data) < OFFSET_CHUNK:
                break
            offset += OFFSET_CHUNK
        encoded_data = json.dumps(list_data)
        self.list_path.write_text(encoded_data)