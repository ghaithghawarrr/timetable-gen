from datetime import time
import json
from timetable_generator import TimetableGenerator
from models import RoomType, SessionType, MainGroup, WeekPattern, SubjectLevel, TimeSlot, Room, Professor, Session

def load_config():
    with open('config.json', 'r') as f:
        return json.load(f)

def create_sample_data():
    # Read the configuration
    with open('config.json', 'r') as f:
        config = json.load(f)
    
    # Create rooms - use a default list if no rooms are specified
    rooms = [
        Room("Room1", RoomType.TD_ROOM, 30, {"standard"}),
        Room("Room2", RoomType.TD_ROOM, 25, {"standard"}),
        Room("Room3", RoomType.TD_ROOM, 40, {"standard"})
    ]
    
    # Create default available slots
    def create_default_slots():
        available_slots = set()
        for day in range(5):  # Monday to Friday
            for hour in range(8, 18, 2):  # 8 AM to 6 PM
                start = time(hour, 30)
                end = time(hour + 1, 45)
                available_slots.add(TimeSlot(start, end, day, WeekPattern.WEEKLY))
        return available_slots
    
    # Create default subject levels
    def create_default_subject_levels(speciality):
        return {
            SubjectLevel(subject="Mathematics", grade=1, speciality=speciality),
            SubjectLevel(subject="Computer Science", grade=1, speciality=speciality),
            SubjectLevel(subject="Physics", grade=1, speciality=speciality)
        }
    
    # Create professors - use a default list if no professors are specified
    professors = [
        Professor(
            id="Prof1", 
            name="Mathematics Professor", 
            subject_levels=create_default_subject_levels("Mathematics"),
            available_slots=create_default_slots(),
            preferred_slots=set(),
            max_hours_per_day=6
        ),
        Professor(
            id="Prof2", 
            name="Computer Science Professor", 
            subject_levels=create_default_subject_levels("Computer Science"),
            available_slots=create_default_slots(),
            preferred_slots=set(),
            max_hours_per_day=6
        ),
        Professor(
            id="Prof3", 
            name="Physics Professor", 
            subject_levels=create_default_subject_levels("Physics"),
            available_slots=create_default_slots(),
            preferred_slots=set(),
            max_hours_per_day=6
        )
    ]
    
    # Create sessions from the config
    sessions = []
    for session_data in config.get('sessions', []):
        # We'll need to modify this to match the Session constructor
        # This is a placeholder and will likely need more work
        session = Session(
            id=session_data['id'],
            subject=session_data['subject'],
            type=SessionType[session_data['type']],
            room_type=RoomType.TD_ROOM,  # default room type
            professor=professors[0],  # default professor
            group=MainGroup(  # default group
                id="DefaultGroup", 
                name="Default", 
                size=30, 
                grade=1, 
                speciality="CS"
            ),
            required_features=set(),
            week_pattern=WeekPattern.WEEKLY,
            priority=1
        )
        sessions.append(session)
    
    return rooms, professors, sessions

def format_day(day: int) -> str:
    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
    return days[day]

def format_time(t: time) -> str:
    return t.strftime("%H:%M")

def main():
    # Create the timetable generator
    generator = TimetableGenerator()
    
    # Get sample data
    rooms, professors, sessions = create_sample_data()
    
    # Generate the timetable
    print("Generating timetable...")
    timetable = generator.generate_timetable(sessions, rooms, professors)
    
    if timetable:
        print("\nTimetable generated successfully!")
        print("\nSchedule:")
        print("-" * 80)
        
        # Sort by day and time for better readability
        sorted_sessions = sorted(
            timetable.items(),
            key=lambda x: (x[1]['day'], x[1]['start_time'])
        )
        
        for session_id, schedule in sorted_sessions:
            # Find the corresponding session object
            session = next(s for s in sessions if s.id == session_id)
            
            print(f"Session: {session.subject} ({session.type.value})")
            print(f"Group: {session.group.id}")
            print(f"Professor: {session.professor.name}")
            print(f"Day: {format_day(schedule['day'])}")
            print(f"Time: {format_time(schedule['start_time'])}")
            print(f"Room: {schedule['room']}")
            if session.week_pattern != WeekPattern.WEEKLY:
                print(f"Week: {session.week_pattern.value}")
            print("-" * 80)
    else:
        print("Failed to generate timetable. Please check constraints.")

if __name__ == "__main__":
    main()
