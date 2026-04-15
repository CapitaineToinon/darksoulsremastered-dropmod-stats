from pydantic import BaseModel, Field


class GameNames(BaseModel):
    international: str
    japanese: str | None
    twitch: str | None


class GameRuleset(BaseModel):
    show_milliseconds: bool = Field(alias="show-milliseconds")
    require_verification: bool = Field(alias="require-verification")
    require_video: bool = Field(alias="require-video")
    run_times: list[str] = Field(alias="run-times")
    default_time: str = Field(alias="default-time")
    emulators_allowed: bool = Field(alias="emulators-allowed")


class Asset(BaseModel):
    uri: str | None


class GameAssets(BaseModel):
    logo: Asset
    cover_tiny: Asset = Field(alias="cover-tiny")
    cover_small: Asset = Field(alias="cover-small")
    cover_medium: Asset = Field(alias="cover-medium")
    cover_large: Asset = Field(alias="cover-large")
    icon: Asset
    background: Asset
    foreground: Asset


class GameLink(BaseModel):
    rel: str
    uri: str


class Game(BaseModel):
    id: str
    names: GameNames
    abbreviation: str
    weblink: str
    discord: str | None
    released: int
    release_date: str = Field(alias="release-date")
    ruleset: GameRuleset
    romhack: bool
    platforms: list[str]
    moderators: dict[str, str]
    created: str | None
    assets: GameAssets
    links: list[GameLink]


class GameResponse(BaseModel):
    data: Game


class GameListResponse(BaseModel):
    data: list[Game]
