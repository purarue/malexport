import json
from typing import NamedTuple, Union, List, Optional, TypeVar
from datetime import date

from .common import strtobool, parse_short_date
from ..list_type import ListType
from ..common import Json

T = TypeVar("T")


def filter_none(lst: List[Optional[T]]) -> List[T]:
    lst_new: List[T] = []
    for x in lst:
        if x is not None:
            lst_new.append(x)
    return lst_new


class Company(NamedTuple):
    id: int
    name: str

    @staticmethod
    def _parse(company_data: Optional[Json]) -> Optional["Company"]:
        if (
            isinstance(company_data, dict)
            and "id" in company_data
            and "name" in company_data
        ):
            return Company(id=company_data["id"], name=company_data["name"])
        else:

            return None


class Season(NamedTuple):
    year: int
    season: str

    @staticmethod
    def _parse(season_data: Optional[Json]) -> Optional["Season"]:
        if (
            isinstance(season_data, dict)
            and "year" in season_data
            and "season" in season_data
        ):
            return Season(year=season_data["year"], season=season_data["season"])
        else:
            return None


class AnimeEntry(NamedTuple):
    status: str
    score: int
    tags: str
    rewatching: bool
    watched_episodes: int
    title: str
    episodes: int
    airing_status: str
    id: int
    studios: List[Company]
    licensors: List[Company]
    season: Optional[Season]
    has_episode_video: bool
    has_promotion_video: bool
    has_video: bool
    video_url: str
    url: str
    image_path: str
    is_added_to_list: bool
    media_type: str
    rating: str
    start_date: Optional[date]
    finish_date: Optional[date]
    air_start_date: Optional[date]
    air_end_date: Optional[date]
    days: Optional[int]
    storage: str
    priority: str


class MangaEntry(NamedTuple):
    status: str
    score: int
    tags: str
    rereading: bool
    read_chapters: int
    read_volumes: int
    title: str
    chapters: int
    volumes: int
    publishing_status: str
    id: int
    manga_magazines: List[Company]
    url: str
    image_path: str
    is_added_to_list: bool
    media_type: str
    start_date: Optional[date]
    finish_date: Optional[date]
    publish_start_date: Optional[date]
    publish_end_date: Optional[date]
    days: Optional[int]
    retail: str
    priority: str


Entry = Union[AnimeEntry, MangaEntry]


class UserList(NamedTuple):
    list_type: str
    entries: List[Entry]


ANIME_STATUS_MAP = {
    1: "Currently Watching",
    2: "Completed",
    3: "On Hold",
    4: "Dropped",
    6: "Plan to Watch",
}

MANGA_STATUS_MAP = {
    1: "Currently Reading",
    2: "Completed",
    3: "On Hold",
    4: "Dropped",
    6: "Plan to Read",
}

ANIME_AIRING_STATUS_MAP = {
    1: "Currently Airing",
    2: "Finished Airing",
    3: "Not Yet Aired",
}

MANGA_PUBLISHING_STATUS_MAP = {
    1: "Currently Publishing",
    2: "Finished Publishing",
    3: "Not Yet Published",
    4: "On Hiatus",
    5: "Discontinued",
}


def _parse_anime(el: Json) -> AnimeEntry:
    return AnimeEntry(
        status=ANIME_STATUS_MAP[el["status"]],
        score=el["score"],
        tags=el["tags"],
        rewatching=strtobool(el["is_rewatching"]),
        watched_episodes=el["num_watched_episodes"],
        title=el["anime_title"],
        episodes=el["anime_num_episodes"],
        airing_status=ANIME_AIRING_STATUS_MAP[el["anime_airing_status"]],
        id=el["anime_id"],
        studios=filter_none(
            [Company._parse(e) for e in list(el["anime_studios"] or [])]
        ),
        licensors=filter_none(
            [Company._parse(e) for e in list(el["anime_licensors"] or [])]
        ),
        season=Season._parse(el["anime_season"]),
        has_video=el["has_video"],
        video_url=el["video_url"],
        has_episode_video=el["has_episode_video"],
        has_promotion_video=el["has_promotion_video"],
        url=el["anime_url"],
        image_path=el["anime_image_path"],
        is_added_to_list=el["is_added_to_list"],
        media_type=el["anime_media_type_string"],
        rating=el["anime_mpaa_rating_string"],
        start_date=parse_short_date(el["start_date_string"] or ""),
        finish_date=parse_short_date(el["finish_date_string"] or ""),
        air_start_date=parse_short_date(el["anime_start_date_string"]),
        air_end_date=parse_short_date(el["anime_end_date_string"]),
        days=el["days_string"],
        storage=el["storage_string"],
        priority=el["priority_string"],
    )


def _parse_manga(el: Json) -> MangaEntry:
    return MangaEntry(
        status=MANGA_STATUS_MAP[el["status"]],
        score=el["score"],
        tags=el["tags"],
        rereading=strtobool(el["is_rereading"]),
        read_chapters=el["num_read_chapters"],
        read_volumes=el["num_read_volumes"],
        title=el["manga_title"],
        chapters=el["manga_num_chapters"],
        volumes=el["manga_num_volumes"],
        publishing_status=MANGA_PUBLISHING_STATUS_MAP[el["manga_publishing_status"]],
        id=el["manga_id"],
        manga_magazines=filter_none(
            [Company._parse(e) for e in list(el["manga_magazines"] or [])]
        ),
        url=el["manga_url"],
        image_path=el["manga_image_path"],
        is_added_to_list=el["is_added_to_list"],
        media_type=el["manga_media_type_string"],
        start_date=parse_short_date(el["start_date_string"] or ""),
        finish_date=parse_short_date(el["finish_date_string"] or ""),
        publish_start_date=parse_short_date(el["manga_start_date_string"]),
        publish_end_date=parse_short_date(el["manga_end_date_string"]),
        days=el["days_string"],
        retail=el["retail_string"],
        priority=el["priority_string"],
    )


def parse_file(json_file: str, list_type: ListType) -> UserList:
    with open(json_file) as f:
        data = json.load(f)
    entries: List[Entry]
    if list_type == ListType.ANIME:
        entries = [_parse_anime(el) for el in data]
    else:
        entries = [_parse_manga(el) for el in data]
    return UserList(list_type=list_type.value.lower(), entries=entries)
