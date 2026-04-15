from pydantic import BaseModel


class RunStatus(BaseModel):
    status: str


class RunSystem(BaseModel):
    platform: str | None = None


class Run(BaseModel):
    id: str
    category: str
    date: str | None
    status: RunStatus
    values: dict[str, str]
    system: RunSystem


class Pagination(BaseModel):
    offset: int
    max: int
    size: int


class RunListResponse(BaseModel):
    data: list[Run]
    pagination: Pagination
