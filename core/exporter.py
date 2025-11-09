from reportlab.platypus import SimpleDocTemplate, Paragraph, Table, TableStyle
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from typing import List, Dict, Any
from .json_parser import TimetableJSONParser
from .data_models import Teacher, Subject, Section, Room


def export_section_pdf(section_name, schedule, path):
    doc = SimpleDocTemplate(f"{path}/Timetable_{section_name}.pdf", pagesize=letter)
    styles = getSampleStyleSheet()
    elements = [Paragraph(f"Timetable - {section_name}", styles["Title"])]

    table_data = [["Day"] + [f"Slot {i+1}" for i in range(6)]]
    for day, slots in schedule.items():
        table_data.append([day] + slots)

    table = Table(table_data)
    table.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 1, colors.black),
        ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
    ]))
    elements.append(table)  # type: ignore
    doc.build(elements) # type: ignore


def export_to_json(
    path: str,
    teachers: List[Teacher],
    subjects: List[Subject],
    sections: List[Section],
    rooms: List[Room],
) -> None:
    """
    Serializes the given data and saves it to a JSON file.

    Args:
        path: The file path to save the JSON data to.
        teachers: A list of Teacher objects.
        subjects: A list of Subject objects.
        sections: A list of Section objects.
        rooms: A list of Room objects.
    """
    serialized_data = TimetableJSONParser.serialize_data(
        teachers, subjects, sections, rooms
    )
    TimetableJSONParser.save_to_json(path, serialized_data)
