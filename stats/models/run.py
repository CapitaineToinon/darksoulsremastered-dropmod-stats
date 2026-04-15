from pydantic import BaseModel


class RunStatus(BaseModel):
    status: str


class Run(BaseModel):
    id: str
    category: str
    date: str | None
    status: RunStatus
    values: dict[str, str]


class Pagination(BaseModel):
    offset: int
    max: int
    size: int


class RunListResponse(BaseModel):
    data: list[Run]
    pagination: Pagination
