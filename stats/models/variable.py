from pydantic import BaseModel, Field


class VariableValueDetail(BaseModel):
    label: str


class VariableValuesMap(BaseModel):
    values: dict[str, VariableValueDetail]


class Variable(BaseModel):
    id: str
    name: str
    is_subcategory: bool = Field(alias="is-subcategory")
    values: VariableValuesMap


class VariableListResponse(BaseModel):
    data: list[Variable]
