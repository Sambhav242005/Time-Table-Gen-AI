from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional

class CourseType(Enum):
    SUBJECT = "SUBJECT"
    LAB = "LAB"

class RoomType(Enum):
    CLASSROOM = "CLASSROOM"
    LAB = "LAB"

@dataclass
class Teacher:
    id: int
    name: str
    code: str
    max_daily_load: int = 6
    max_weekly_load: int = 20
    availability: Dict[str, List[int]] = field(default_factory=dict)

@dataclass
class Subject:
    id: int
    code: str
    name: str
    credits: int
    weekly_lecture_slots: int
    is_lab: bool = False

@dataclass
class Section:
    id: int
    name: str
    semester: int
    strength: int

@dataclass
class Room:
    id: int
    name: str
    capacity: int
    type: RoomType
    lab_type: Optional[str] = None
