from pydantic import BaseModel


class Platform(BaseModel):
    id: str
    name: str


class PlatformResponse(BaseModel):
    data: Platform
