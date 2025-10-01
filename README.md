# Advanced Timetable Generator

A comprehensive PyQt5-based application for generating optimized timetables for educational institutions with multi-constraint optimization and conflict resolution.

## Features

- **Multi-Entity Management**: Manage teachers, subjects, sections, and rooms with detailed configurations
- **Intelligent Scheduling**: Advanced constraint-based timetable generation with conflict resolution
- **Parallel Processing**: Efficient generation using background threads for better performance
- **Multiple Views**: View timetables by section, teacher, or room
- **PDF Export**: Export all timetables as professional PDF documents
- **Lab Course Support**: Special handling for laboratory courses with block scheduling
- **Flexible Configuration**: Customizable working days, slots per day, and optimization strategies
- **Sample Data**: Quick setup with sample data for testing and demonstration

## Screenshots

*Add screenshots of the application interface here*

## Installation

### Prerequisites

- Python 3.7 or higher
- PyQt5
- ReportLab (for PDF generation)

### Install Dependencies

```bash
pip install PyQt5 reportlab
```

### Run the Application

```bash
python main.py
```

## Usage

1. **Setup Data**: Configure teachers, subjects, sections, and rooms
2. **Generate Timetables**: Select working days and optimization strategy
3. **View Results**: Browse timetables by section, teacher, or room
4. **Export PDFs**: Save all timetables as PDF files

### Quick Start

1. Launch the application
2. Go to SETUP page and initialize sample data
3. Navigate to GENERATE page and click "Generate Timetables"
4. View the results in the VIEW page
5. Export timetables as PDFs

## Project Structure

```
├── main.py                 # Main application file
├── README.md              # Project documentation
└── .gitignore            # Git ignore rules
```

## Dependencies

- PyQt5: GUI framework
- ReportLab: PDF generation
- Python Standard Library modules (sys, random, json, datetime, etc.)

## Features in Detail

### Teacher Management
- Add/edit teacher information
- Configure maximum daily and weekly load
- Set availability constraints

### Subject Management
- Regular subjects with credits and weekly slots
- Lab courses with block scheduling
- Different lab types (Computer Science, Physics, Chemistry, etc.)

### Section Management
- Multiple sections per semester
- Configurable section strength
- Semester-wise organization

### Room Management
- Classrooms and laboratories
- Capacity management
- Lab type specifications

### Timetable Generation
- Multi-constraint optimization
- Conflict resolution algorithms
- Parallel processing for efficiency
- Progress tracking and status updates

### Export Features
- Section timetables
- Teacher timetables
- Room timetables
- Professional PDF formatting

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For support and questions, please open an issue on the GitHub repository.

## Version

Current Version: 2.0

## Author

Academic Solutions Team
