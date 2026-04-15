from pydantic import BaseModel


class Category(BaseModel):
    id: str
    name: str
    miscellaneous: bool


class CategoryListResponse(BaseModel):
    data: list[Category]
