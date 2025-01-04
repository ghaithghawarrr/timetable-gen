from ortools.sat.python import cp_model
from typing import List, Dict
from datetime import time
from models import TDGroup, TPGroup, MainGroup, Session, TimeSlot, WeekPattern, Professor, Room

class TimetableGenerator:
    def __init__(self):
        self.model = cp_model.CpModel()
        self.solver = cp_model.CpSolver()
        
        # Initialize working hours
        self.working_hours = {
            'start': time(8, 30),
            'end': time(18, 45),
            'lunch_start': time(11, 30),
            'lunch_end': time(13, 30),
            'restaurant_start': time(17, 0),
            'restaurant_end': time(19, 0)
        }
        
        # Initialize time slots
        self.time_slots: List[TimeSlot] = []
        
    def _create_time_slots(self, include_biweekly=False) -> List[TimeSlot]:
        """Create all possible time slots for the week"""
        slots = []
        days = range(5)  # Monday to Friday
        weeks = [WeekPattern.WEEKLY] if not include_biweekly else [WeekPattern.WEEKLY, WeekPattern.BIWEEKLY_A, WeekPattern.BIWEEKLY_B]
        
        for week in weeks:
            for day in days:
                for hour in range(8, 17):  # 8 AM to 5 PM
                    if hour != 12:  # Skip lunch hour
                        slots.append(TimeSlot(
                            time(hour, 30),
                            time((hour + 1) % 24, 45),
                            day,
                            week
                        ))
        print(f"Generated {len(slots)} time slots")
        return slots

    def generate_timetable(self, sessions: List[Session], rooms: List[Room], 
                          professors: List[Professor]) -> Dict:
        """Generate a timetable for the given sessions, rooms, and professors"""
        print("Generating timetable...")
        print(f"Generating timetable for {len(sessions)} sessions, {len(rooms)} rooms, and {len(professors)} professors")
        
        # Create time slots
        self.time_slots = self._create_time_slots()
        print(f"Available time slots: {len(self.time_slots)}")
        
        # Create the solver
        self.model = cp_model.CpModel()
        
        # Create assignment variables
        assignments = {}  # (session_id, day, time, room_id) -> var
        for session in sessions:
            for slot in self.time_slots:
                # Check if professor is available for this slot
                prof_available = False
                for avail_slot in session.professor.available_slots:
                    if (slot.day == avail_slot.day and
                        slot.start_time == avail_slot.start_time and
                        slot.end_time == avail_slot.end_time):
                        prof_available = True
                        break
                
                if not prof_available:
                    continue
                
                for room in rooms:
                    if room.type == session.room_type:
                        var_name = f"{session.id}_{slot.day}_{slot.start_time.hour:02d}{slot.start_time.minute:02d}_{room.id}"
                        assignments[var_name] = self.model.NewBoolVar(var_name)
        
        print(f"Created {len(assignments)} assignment variables")
        
        # Add constraints
        self._add_session_constraints(assignments, sessions)
        self._add_room_constraints(assignments, rooms)
        self._add_professor_constraints(assignments, sessions, professors)
        self._add_room_capacity_constraints(assignments, sessions, rooms)
        self._add_student_group_constraints(assignments, sessions)
        self._add_professor_workload_constraints(assignments, sessions, professors)
        
        # Add objective: maximize priority sessions in preferred slots
        objective = self.model.NewIntVar(0, 1000000, 'objective')
        objective_terms = []
        
        for var_name, var in assignments.items():
            # Extract session and slot information from variable name
            try:
                parts = var_name.split('_')
                if len(parts) < 4:
                    continue
                    
                # Handle session IDs that might contain underscores
                time_str = parts[-2]
                room_id = parts[-1]
                day = int(parts[-3])
                session_id = '_'.join(parts[:-3])
                
                # Parse time
                hour = int(time_str[:2])
                minute = int(time_str[2:])
                slot_time = time(hour, minute)
                
                # Find matching session
                session = next((s for s in sessions if s.id == session_id), None)
                if session:
                    # Add priority weight
                    objective_terms.append(var * session.priority * 10)
                    
                    # Add preferred slot bonus
                    slot = TimeSlot(slot_time, None, day)  # end_time not needed for comparison
                    if slot in session.professor.preferred_slots:
                        objective_terms.append(var * 5)
            except (ValueError, IndexError) as e:
                print(f"Warning: Could not parse variable name {var_name}: {e}")
                continue
        
        self.model.Add(objective == sum(objective_terms))
        self.model.Maximize(objective)
        
        # Solve the model
        status = self.solver.Solve(self.model)
        status_name = "UNKNOWN"
        if status == cp_model.OPTIMAL:
            status_name = "OPTIMAL"
        elif status == cp_model.FEASIBLE:
            status_name = "FEASIBLE"
        elif status == cp_model.INFEASIBLE:
            status_name = "INFEASIBLE"
        elif status == cp_model.MODEL_INVALID:
            status_name = "MODEL_INVALID"
        
        print(f"Solver status: {status_name}")
        
        if status == cp_model.OPTIMAL or status == cp_model.FEASIBLE:
            solution = self._extract_solution(assignments)
            if solution:
                print("Found valid solution!")
                return solution
        print("No valid solution found. Constraints might be too restrictive.")
        return None

    def _extract_solution(self, assignments: Dict) -> Dict:
        """Extract the solution from the solver"""
        solution = {}
        try:
            for var_name, var in assignments.items():
                if self.solver.Value(var) == 1:
                    print(f"Found assignment: {var_name}")
                    # Split carefully considering the format: sessionid_day_HHMM_roomid
                    parts = var_name.split('_')
                    if len(parts) < 4:
                        print(f"Warning: Unexpected variable name format: {var_name}")
                        continue
                    
                    # Handle session IDs that might contain underscores
                    time_str = parts[-2]
                    room_id = parts[-1]
                    day = parts[-3]
                    session_id = '_'.join(parts[:-3])
                    
                    # Convert time string (HHMM) to time object
                    try:
                        hour = int(time_str[:2])
                        minute = int(time_str[2:])
                        slot_time = time(hour, minute)
                    except (ValueError, IndexError) as e:
                        print(f"Warning: Invalid time format in {var_name}: {e}")
                        continue
                    
                    solution[session_id] = {
                        'day': int(day),
                        'start_time': slot_time,
                        'room': room_id
                    }
            
            if not solution:
                print("Warning: No valid assignments found in solution")
            return solution
            
        except Exception as e:
            print(f"Error extracting solution: {e}")
            return None

    def _add_session_constraints(self, assignments: Dict, sessions: List[Session]):
        """Add constraints related to sessions"""
        print("Adding session constraints...")
        
        # Each session must be scheduled exactly once
        for session in sessions:
            session_vars = []
            for var_name, var in assignments.items():
                if var_name.startswith(session.id):
                    session_vars.append(var)
            if not session_vars:
                print(f"Warning: No valid slots found for session {session.id}")
                continue
            print(f"Found {len(session_vars)} possible slots for session {session.id}")
            self.model.Add(sum(session_vars) == 1)
        
        # Sessions of the same subject should not be at the same time
        for slot in self.time_slots:
            slot_pattern = f"_{slot.day}_{slot.start_time.hour:02d}{slot.start_time.minute:02d}_"
            for subject in set(session.subject for session in sessions):
                subject_slot_vars = []
                for var_name, var in assignments.items():
                    session_id = var_name.split('_')[0]
                    for session in sessions:
                        if session.id == session_id and session.subject == subject and slot_pattern in var_name:
                            subject_slot_vars.append(var)
                if subject_slot_vars:
                    # At most one session per subject at a time
                    self.model.Add(sum(subject_slot_vars) <= 1)

    def _add_room_constraints(self, assignments: Dict, rooms: List[Room]):
        """Add constraints related to room usage"""
        print("Adding room constraints...")
        
        # Group assignments by time slot and room
        for slot in self.time_slots:
            for room in rooms:
                # Get all assignments for this room and time slot
                slot_room_vars = []
                for var_name, var in assignments.items():
                    if f"_{slot.day}_{slot.start_time.hour:02d}{slot.start_time.minute:02d}_{room.id}" in var_name:
                        slot_room_vars.append(var)
                # Ensure at most one session per room per time slot
                if slot_room_vars:
                    self.model.Add(sum(slot_room_vars) <= 1)

    def _add_professor_constraints(self, assignments: Dict, sessions: List[Session], professors: List[Professor]):
        """Add constraints related to professor availability"""
        print("Adding professor constraints...")
        
        for professor in professors:
            slots_available = 0
            for slot in self.time_slots:
                # Get all variables for this professor in this time slot
                slot_pattern = f"_{slot.day}_{slot.start_time.hour:02d}{slot.start_time.minute:02d}_"
                prof_slot_vars = []
                
                for var_name, var in assignments.items():
                    if slot_pattern in var_name:
                        session_id = var_name.split('_')[0]
                        session = next((s for s in sessions if s.id == session_id), None)
                        if session and session.professor.id == professor.id:
                            # Check if professor can teach this subject
                            if not session.professor.can_teach(session.subject, session.group.grade, session.group.speciality):
                                self.model.Add(var == 0)
                                continue
                            prof_slot_vars.append(var)
                
                # Check professor availability for this slot
                is_available = False
                for avail_slot in professor.available_slots:
                    if (slot.day == avail_slot.day and
                        slot.start_time == avail_slot.start_time and
                        slot.end_time == avail_slot.end_time):
                        is_available = True
                        slots_available += 1
                        break
                
                if not is_available:
                    # Professor is not available, forbid all assignments
                    for var in prof_slot_vars:
                        self.model.Add(var == 0)
            
            print(f"Professor {professor.id} has {slots_available} available slots")

    def _add_room_capacity_constraints(self, assignments: Dict, sessions: List[Session], rooms: List[Room]):
        """Add constraints for room capacity"""
        print("Adding room capacity constraints...")
        
        for slot in self.time_slots:
            for room in rooms:
                slot_pattern = f"_{slot.day}_{slot.start_time.hour:02d}{slot.start_time.minute:02d}_{room.id}"
                for var_name, var in assignments.items():
                    if slot_pattern in var_name:
                        session_id = var_name.split('_')[0]
                        for session in sessions:
                            if session.id == session_id:
                                # Room must have sufficient capacity
                                if session.group.size > room.capacity:
                                    self.model.Add(var == 0)
                                # Room must have required features
                                if not session.required_features.issubset(room.features):
                                    print(f"Room {room.id} missing features {session.required_features - room.features} for session {session.id}")
                                    self.model.Add(var == 0)

    def _add_student_group_constraints(self, assignments: Dict, sessions: List[Session]):
        """Prevent scheduling conflicts for student groups"""
        print("Adding student group constraints...")
        
        for slot in self.time_slots:
            slot_pattern = f"_{slot.day}_{slot.start_time.hour:02d}{slot.start_time.minute:02d}_"
            
            # Group sessions by their groups
            groups_in_slot = {}
            for var_name, var in assignments.items():
                if slot_pattern in var_name:
                    session_id = var_name.split('_')[0]
                    session = next((s for s in sessions if s.id == session_id), None)
                    if session:
                        group_id = session.group.id
                        if group_id not in groups_in_slot:
                            groups_in_slot[group_id] = []
                        groups_in_slot[group_id].append(var)
            
            # Add constraints to prevent concurrent sessions for the same group
            for group_id, vars_list in groups_in_slot.items():
                if len(vars_list) > 1:
                    # At most one session can be scheduled for this group in this time slot
                    self.model.Add(sum(vars_list) <= 1)

    def _add_professor_workload_constraints(self, assignments: Dict, sessions: List[Session], professors: List[Professor]):
        """Limit professor teaching hours per day"""
        print("Adding professor workload constraints...")
        
        for professor in professors:
            for day in range(5):  # Monday to Friday
                day_slots = []
                for var_name, var in assignments.items():
                    if f"_{day}_" in var_name:
                        session_id = var_name.split('_')[0]
                        for session in sessions:
                            if (session.id == session_id and 
                                session.professor.id == professor.id):
                                day_slots.append(var)
                if day_slots:
                    # Each session is 1.5 hours, so multiply max_hours by 2/3
                    max_sessions = int(professor.max_hours_per_day * 2 / 3)
                    print(f"Professor {professor.id} limited to {max_sessions} sessions on day {day}")
                    self.model.Add(sum(day_slots) <= max_sessions)
