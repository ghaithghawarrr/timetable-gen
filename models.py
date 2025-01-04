from dataclasses import dataclass, field
from typing import List, Dict, Set, Optional, Union
from datetime import datetime, time
from enum import Enum, auto

class RoomType(Enum):
    AMPHI = "amphi"
    TD_ROOM = "td_room"
    LAB = "lab"

class SessionType(Enum):
    COURS = "cours"
    TD = "td"
    TP = "tp"

class WeekPattern(Enum):
    WEEKLY = "weekly"
    BIWEEKLY_A = "week_a"
    BIWEEKLY_B = "week_b"

@dataclass(frozen=True)
class TimeSlot:
    start_time: time
    end_time: time
    day: int  # 0-4 for Monday-Friday
    week: WeekPattern = WeekPattern.WEEKLY

    def __eq__(self, other):
        if not isinstance(other, TimeSlot):
            return False
        return (self.start_time == other.start_time and
                self.end_time == other.end_time and
                self.day == other.day and
                self.week == other.week)

    def __hash__(self):
        return hash((self.start_time, self.end_time, self.day, self.week))

    def overlaps(self, other: 'TimeSlot') -> bool:
        """Check if this time slot overlaps with another"""
        if self.day != other.day:
            return False
        if self.week != other.week and self.week != WeekPattern.WEEKLY and other.week != WeekPattern.WEEKLY:
            return False
        return (self.start_time < other.end_time and 
                self.end_time > other.start_time)

@dataclass(frozen=True)
class SubjectLevel:
    subject: str
    grade: int  # Year level (1, 2, 3, etc.)
    speciality: str  # e.g., "CS", "Math", "Physics"

    def __hash__(self):
        return hash((self.subject, self.grade, self.speciality))

    def __eq__(self, other):
        if not isinstance(other, SubjectLevel):
            return NotImplemented
        return (self.subject == other.subject and 
                self.grade == other.grade and 
                self.speciality == other.speciality)

@dataclass(frozen=True)
class TPGroup:
    id: str
    name: str
    size: int
    grade: int
    speciality: str
    parent_td: Optional['TDGroup'] = None

    def __hash__(self):
        return hash(self.id)

    def __eq__(self, other):
        if not isinstance(other, TPGroup):
            return NotImplemented
        return self.id == other.id

@dataclass(frozen=True)
class TDGroup:
    id: str
    name: str
    size: int
    grade: int
    speciality: str
    tp_groups: List[TPGroup] = field(default_factory=list)
    parent_group: Optional['MainGroup'] = None

    def __hash__(self):
        return hash(self.id)

    def __eq__(self, other):
        if not isinstance(other, TDGroup):
            return NotImplemented
        return self.id == other.id

    def __post_init__(self):
        if self.tp_groups:
            object.__setattr__(self, 'tp_groups', [
                TPGroup(g.id, g.name, g.size, self.grade, self.speciality, self) if isinstance(g, TPGroup)
                else TPGroup(g['id'], g['name'], g['size'], self.grade, self.speciality, self)
                for g in self.tp_groups
            ])

@dataclass(frozen=True)
class MainGroup:
    id: str
    name: str
    size: int
    grade: int
    speciality: str
    td_groups: List[TDGroup] = field(default_factory=list)

    def __hash__(self):
        return hash(self.id)

    def __eq__(self, other):
        if not isinstance(other, MainGroup):
            return NotImplemented
        return self.id == other.id

    @classmethod
    def create_from_dict(cls, data: Dict) -> 'MainGroup':
        td_groups = []
        total_size = 0

        for td_data in data['td_groups']:
            tp_groups = []
            for tp_name in td_data['tp_groups']:
                tp_groups.append({
                    'id': f"{data['group_name']}.{td_data['td_name']}.{tp_name}",
                    'name': tp_name,
                    'size': 1  # Assuming each TP group has size 1 for simplicity
                })
            
            td_group = TDGroup(
                id=f"{data['group_name']}.{td_data['td_name']}",
                name=td_data['td_name'],
                size=len(td_data['tp_groups']),
                grade=data['grade'],
                speciality=data['speciality'],
                tp_groups=tp_groups
            )
            td_groups.append(td_group)
            total_size += len(tp_groups)

        main_group = cls(
            id=data['group_name'],
            name=data['group_name'],
            size=total_size,
            grade=data['grade'],
            speciality=data['speciality'],
            td_groups=td_groups
        )

        # Update parent references
        for td in main_group.td_groups:
            object.__setattr__(td, 'parent_group', main_group)
            for tp in td.tp_groups:
                object.__setattr__(tp, 'parent_td', td)

        return main_group

@dataclass
class Room:
    id: str
    type: RoomType
    capacity: int
    features: Set[str] = field(default_factory=set)

@dataclass
class Professor:
    id: str
    name: str
    subject_levels: Set[SubjectLevel]  # List of subjects with grade levels
    available_slots: Set[TimeSlot]
    preferred_slots: Set[TimeSlot] = field(default_factory=set)
    max_hours_per_day: int = 6

    def __post_init__(self):
        if not isinstance(self.subject_levels, set):
            object.__setattr__(self, 'subject_levels', set(self.subject_levels))
        if not isinstance(self.available_slots, set):
            object.__setattr__(self, 'available_slots', set(self.available_slots))
        if not isinstance(self.preferred_slots, set):
            object.__setattr__(self, 'preferred_slots', set(self.preferred_slots))

    def can_teach(self, subject: str, grade: int, speciality: str) -> bool:
        return any(sl.subject == subject and sl.grade == grade and sl.speciality == speciality 
                  for sl in self.subject_levels)

@dataclass
class Session:
    id: str
    subject: str
    type: SessionType
    room_type: RoomType
    professor: Professor
    group: Union[MainGroup, TDGroup, TPGroup]
    required_features: Set[str] = field(default_factory=set)
    week_pattern: WeekPattern = WeekPattern.WEEKLY
    priority: int = 1

    def __post_init__(self):
        if not isinstance(self.required_features, set):
            object.__setattr__(self, 'required_features', set(self.required_features))
