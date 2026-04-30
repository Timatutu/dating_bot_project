from pydantic import BaseModel, Field


class ItemOut(BaseModel):
    id: int
    name: str
    value: str
    updated_at: float


class ItemWrite(BaseModel):
    value: str = Field(..., min_length=1, max_length=500)


class ResetRequest(BaseModel):
    dataset_size: int = Field(1000, ge=1, le=100000)

