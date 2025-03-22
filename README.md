# QR-Based Attendance System

A modern, secure, and efficient attendance tracking system using QR codes. Built with Flask, SQLite, and Bootstrap.

## Features

- 🔐 Separate Admin & Student Authentication
- 📱 QR Code Generation & Scanning
- 📊 Real-time Attendance Tracking
- 📑 Session Management & Report Generation
- 💻 Responsive Design
- 🔒 Secure Authentication

## Prerequisites

- Python 3.8 or higher
- pip (Python package manager)

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd qr-attendance-system
```

2. Create a virtual environment and activate it:
```bash
python -m venv venv
.\venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/Mac
```

3. Install the required packages:
```bash
pip install -r requirements.txt
```

## Usage

1. Start the Flask application:
```bash
python app.py
```

2. Open your web browser and navigate to:
```
http://localhost:5000
```

## Admin Access

- Username: ********
- Password: ********


## Student Access

1. Register as a new student
2. Login with your roll number and password
3. Download your unique QR code
4. Show QR code to admin during attendance sessions

## Features

### Admin Features
- Start/End attendance sessions
- Scan student QR codes
- View real-time attendance updates
- Generate attendance reports

### Student Features
- Secure registration and login
- Generate unique QR code
- Download QR code
- View personal details

## Security Features

- Password hashing
- Session management
- CSRF protection
- Secure QR code generation

## Contributing

1. Fork the repository
2. Create your feature branch
3. Commit your changes
4. Push to the branch
5. Create a new Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.
