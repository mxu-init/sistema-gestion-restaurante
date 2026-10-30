from pydantic import BaseModel


class TestCreate(BaseModel):
    test_name: str
    test_type: str
