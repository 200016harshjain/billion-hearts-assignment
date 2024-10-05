from pydantic import BaseModel
from typing import Optional,Literal

class ImageUploadRequest(BaseModel):
    user_id: int
    original_filename: str
    width: int
    height: int
    file_size: int
    file_type: Literal['jpeg', 'png']

    class Config:
        extra = "forbid"

class ImageUpdateRequest(BaseModel):
    original_filename: Optional[str] = None
    width: Optional[int] = None
    height: Optional[int] = None
    file_size: Optional[int] = None
    file_type: Optional[Literal['jpeg', 'png']] = None

    class Config:
        extra = "forbid"

class UserCreateRequest(BaseModel):
    id: int
    username: str

    class Config:
        extra = "forbid"