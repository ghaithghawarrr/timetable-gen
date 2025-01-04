# Timetable Generator

An automated timetable generation system built with Python and Google OR-Tools. This project helps educational institutions generate conflict-free timetables while considering various constraints such as room capacity, professor availability, and student group schedules.

## Features

- Automatic scheduling of courses, TD (Tutorial) sessions, and TP (Practical) sessions
- Support for multiple types of rooms (Amphitheater, TD Room, Lab)
- Professor availability and workload management
- Room capacity constraints
- Student group conflict prevention
- Weekly and bi-weekly scheduling patterns
- Configurable through JSON configuration files

## Requirements

- Python 3.9 or higher
- Google OR-Tools (>=9.6.2534)
- python-dateutil (>=2.8.2)

## Installation

1. Clone the repository:
```bash
git clone [your-repo-url]
cd timetable-generator
```

2. Install the required packages:
```bash
pip install -r requirements.txt
```

## Usage

1. Configure your timetable requirements in `config.json`. The configuration file should include:
   - Rooms (type, capacity, features)
   - Professors (availability, subjects, max hours per day)
   - Sessions (type, subject, required features)
   - Student groups

2. Run the example usage:
```bash
python example_usage.py
```

### Docker Support

You can also run the project using Docker:

1. Build the Docker image:
```bash
docker build -t timetable-generator .
```

2. Run the container:
```bash
docker run timetable-generator
```

## Project Structure

- `timetable_generator.py`: Core timetable generation logic using OR-Tools
- `models.py`: Data models for rooms, professors, sessions, and groups
- `example_usage.py`: Example implementation and usage
- `config.json`: Configuration file for timetable requirements
- `requirements.txt`: Python dependencies
- `Dockerfile`: Docker configuration for containerization

## Configuration

The `config.json` file allows you to specify:

- Working hours and break times
- Room details (type, capacity, features)
- Professor information (availability, subjects, workload limits)
- Session requirements (type, subject, room requirements)
- Student group structures (main groups, TD groups, TP groups)

## How It Works

The timetable generator uses Google OR-Tools' constraint programming solver to:

1. Create time slots based on working hours
2. Generate assignment variables for each session
3. Apply constraints:
   - Room availability and capacity
   - Professor availability and workload
   - Student group conflicts
   - Room type requirements
4. Find an optimal solution that satisfies all constraints
