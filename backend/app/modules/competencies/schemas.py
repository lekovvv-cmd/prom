from pydantic import BaseModel


class CompetencyRead(BaseModel):
    name: str
    group: str
