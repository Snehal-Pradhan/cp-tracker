"""Data models shared across the app."""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


@dataclass
class Contest:
    platform: str
    name: str
    start_time: datetime
    duration_minutes: int
    url: str
    id: str = ""

    def to_dict(self):
        d = asdict(self)
        d["start_time"] = self.start_time.timestamp()
        return d

    @classmethod
    def from_dict(cls, d):
        d = dict(d)
        d["start_time"] = datetime.fromtimestamp(d["start_time"], tz=timezone.utc)
        return cls(**d)


@dataclass
class RatingPoint:
    time: datetime
    rating: int

    def to_dict(self):
        return {"time": self.time.timestamp(), "rating": self.rating}

    @classmethod
    def from_dict(cls, d):
        return cls(datetime.fromtimestamp(d["time"], tz=timezone.utc), d["rating"])


@dataclass
class ContestResult:
    date: datetime
    name: str
    rank: int
    delta: int

    def to_dict(self):
        return {"date": self.date.timestamp(), "name": self.name,
                "rank": self.rank, "delta": self.delta}

    @classmethod
    def from_dict(cls, d):
        d = dict(d)
        d["date"] = datetime.fromtimestamp(d["date"], tz=timezone.utc)
        return cls(**d)


@dataclass
class UserStats:
    platform: str
    handle: str
    ok: bool
    error: str = ""
    rating: int | None = None
    max_rating: int | None = None
    rank: str | None = None
    global_rank: int | None = None
    country_rank: int | None = None
    top_percentage: float | None = None
    contests_attended: int | None = None
    solved: dict = field(default_factory=dict)
    history: list[RatingPoint] = field(default_factory=list)
    results: list[ContestResult] = field(default_factory=list)
    extra: dict = field(default_factory=dict)

    def to_dict(self):
        return {
            **asdict(self),
            "history": [p.to_dict() for p in self.history],
            "results": [r.to_dict() for r in self.results],
        }

    @classmethod
    def from_dict(cls, d):
        d = dict(d)
        d["history"] = [RatingPoint.from_dict(p) for p in d.get("history", [])]
        d["results"] = [ContestResult.from_dict(r) for r in d.get("results", [])]
        return cls(**d)


@dataclass
class Store:
    stats: dict = field(default_factory=dict)
    contests: list[Contest] = field(default_factory=list)
    last_updated: float | None = None

    def stat_for(self, key: str) -> UserStats | None:
        return self.stats.get(key)
