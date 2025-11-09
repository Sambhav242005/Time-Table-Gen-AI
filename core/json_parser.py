# core/json_parser.py
import json
import os
from typing import List, Dict, Any, Tuple
from .data_models import Teacher, Subject, Section, Room, RoomType


class TimetableJSONParser:
    """Utility class for serializing and deserializing timetable data."""

    @staticmethod
    def serialize_data(
        teachers: List[Teacher],
        subjects: List[Subject],
        sections: List[Section],
        rooms: List[Room]
    ) -> Dict[str, Any]:
        """Convert Python objects into a structured JSON-compatible dict."""
        return {
            "teachers": [
                {
                    "id": t.id,
                    "name": t.name,
                    "code": t.code,
                    "max_daily_load": t.max_daily_load,
                    "max_weekly_load": t.max_weekly_load
                }
                for t in teachers
            ],
            "subjects": [
                {
                    "id": s.id,
                    "code": s.code,
                    "name": s.name,
                    "credits": s.credits,
                    "weekly_lecture_slots": s.weekly_lecture_slots,
                    "is_lab": s.is_lab
                }
                for s in subjects
            ],
            "sections": [
                {
                    "id": sec.id,
                    "name": sec.name,
                    "semester": sec.semester,
                    "strength": sec.strength
                }
                for sec in sections
            ],
            "rooms": [
                {
                    "id": r.id,
                    "name": r.name,
                    "capacity": r.capacity,
                    "type": r.type.value,
                    "lab_type": r.lab_type
                }
                for r in rooms
            ]
        }

    @staticmethod
    def deserialize_data(data: Dict[str, Any]) -> Tuple[
        List[Teacher], List[Subject], List[Section], List[Room]
    ]:
        """Convert a JSON dictionary back into Python model objects."""
        teachers = [
            Teacher(
                t["id"], t["name"], t["code"],
                t.get("max_daily_load", 6),
                t.get("max_weekly_load", 20)
            )
            for t in data.get("teachers", [])
        ]

        subjects = [
            Subject(
                s["id"], s["code"], s["name"],
                s.get("credits", 3),
                s.get("weekly_lecture_slots", 3),
                s.get("is_lab", False)
            )
            for s in data.get("subjects", [])
        ]

        sections = [
            Section(
                sec["id"], sec["name"],
                sec.get("semester", 1),
                sec.get("strength", 60)
            )
            for sec in data.get("sections", [])
        ]

        rooms = [
            Room(
                r["id"], r["name"],
                r.get("capacity", 60),
                RoomType(r.get("type", "CLASSROOM")),
                r.get("lab_type", None)
            )
            for r in data.get("rooms", [])
        ]

        return teachers, subjects, sections, rooms

    @staticmethod
    def save_to_json(path: str, data: Dict[str, Any]) -> None:
        """Save structured data to a JSON file."""
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)

    @staticmethod
    def load_from_json(path: str) -> Dict[str, Any]:
        """Load JSON data from a file."""
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
