# core/dataframe_parser.py
import pandas as pd
from typing import List, Type, TypeVar, Optional, cast
from .data_models import Teacher, Subject, Section, Room, RoomType

T = TypeVar("T")


def dataframe_to_objects(df: pd.DataFrame, obj_type: Type[T]) -> List[T]:
    """
    Converts a pandas DataFrame to a list of structured Python objects.
    This function provides type-safe conversion for supported dataclasses.

    Args:
        df: The DataFrame to convert.
        obj_type: The dataclass type to convert each row into.

    Returns:
        A list of dataclass instances of type T.

    Raises:
        ValueError: If the object type is not supported.
    """
    objects: List[T] = []
    for _, row in df.iterrows():
        try:
            if obj_type is Room:
                obj = cast(
                    T,
                    Room(
                        id=int(row["id"]),
                        name=str(row["name"]),
                        capacity=int(row["capacity"]),
                        type=RoomType(str(row["type"])),
                        lab_type=cast(Optional[str], row.get("lab_type")),
                    ),
                )
            elif obj_type is Teacher:
                obj = cast(
                    T,
                    Teacher(
                        id=int(row["id"]),
                        name=str(row["name"]),
                        code=str(row["code"]),
                        max_daily_load=int(row.get("max_daily_load", 6)),
                        max_weekly_load=int(row.get("max_weekly_load", 20)),
                    ),
                )
            elif obj_type is Subject:
                obj = cast(
                    T,
                    Subject(
                        id=int(row["id"]),
                        code=str(row["code"]),
                        name=str(row["name"]),
                        credits=int(row.get("credits", 3)),
                        weekly_lecture_slots=int(
                            row.get("weekly_lecture_slots", 3)
                        ),
                        is_lab=bool(row.get("is_lab", False)),
                    ),
                )
            elif obj_type is Section:
                obj = cast(
                    T,
                    Section(
                        id=int(row["id"]),
                        name=str(row["name"]),
                        semester=int(row.get("semester", 1)),
                        strength=int(row.get("strength", 60)),
                    ),
                )
            else:
                # Fallback for any other dataclass, less safe
                row_dict = row.to_dict()
                obj = cast(T, obj_type(**row_dict))

            objects.append(obj)
        except (KeyError, TypeError, ValueError) as e:
            raise ValueError(
                f"Failed to convert row to {obj_type.__name__}: {row.to_dict()}. Error: {e}"
            )

    return objects
