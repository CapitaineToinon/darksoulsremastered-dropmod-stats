from pydantic import BaseModel


class RunStatus(BaseModel):
    status: str


class RunPlayer(BaseModel):
    rel: str
    id: str | None = None    # present for registered users, absent for guests


class RunSystem(BaseModel):
    platform: str | None = None


class RunTimes(BaseModel):
    primary_t: float
    realtime_t: float
    ingame_t: float


class Run(BaseModel):
    id: str
    category: str
    date: str | None
    status: RunStatus
    values: dict[str, str]
    system: RunSystem
    times: RunTimes
    players: list[RunPlayer]


class Pagination(BaseModel):
    offset: int
    max: int
    size: int


class RunListResponse(BaseModel):
    data: list[Run]
    pagination: Pagination
