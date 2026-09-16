"""Strutture dati condivise tra i raccoglitori e la formattazione."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class PostStats:
    """Statistiche di un singolo post."""

    platform: str
    post_id: str
    published_at: datetime
    caption: str
    permalink: str | None = None
    media_type: str | None = None
    likes: int = 0
    comments: int = 0
    shares: int = 0
    saves: int = 0
    reach: int = 0
    impressions: int = 0
    clicks: int = 0
    video_views: int = 0

    @property
    def interactions(self) -> int:
        return self.likes + self.comments + self.shares + self.saves

    @property
    def engagement_rate(self) -> float | None:
        """Interazioni sulla copertura, in percentuale."""
        if not self.reach:
            return None
        return self.interactions / self.reach * 100


@dataclass
class PlatformReport:
    """Esito della raccolta per una piattaforma."""

    platform: str
    posts: list[PostStats] = field(default_factory=list)
    followers: int | None = None
    error: str | None = None

    @property
    def total_likes(self) -> int:
        return sum(p.likes for p in self.posts)

    @property
    def total_comments(self) -> int:
        return sum(p.comments for p in self.posts)

    @property
    def total_shares(self) -> int:
        return sum(p.shares for p in self.posts)

    @property
    def total_saves(self) -> int:
        return sum(p.saves for p in self.posts)

    @property
    def total_interactions(self) -> int:
        return sum(p.interactions for p in self.posts)

    @property
    def total_reach(self) -> int:
        return sum(p.reach for p in self.posts)

    @property
    def total_impressions(self) -> int:
        return sum(p.impressions for p in self.posts)

    @property
    def best_post(self) -> PostStats | None:
        if not self.posts:
            return None
        return max(self.posts, key=lambda p: (p.interactions, p.reach))
