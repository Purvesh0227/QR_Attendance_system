from flask import Flask, render_template, request, redirect, url_for, flash, session as flask_session, g, jsonify, Response, send_file
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import qrcode
from io import BytesIO
import base64
import os
import csv
from io import StringIO

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key'
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{os.path.join(os.path.abspath(os.path.dirname(__file__)), "instance", "database.db")}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Models
class Student(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    roll_number = db.Column(db.String(20), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
    college_name = db.Column(db.String(200), nullable=False)
    attendances = db.relationship('Attendance', backref='student', lazy=True)

class Admin(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)

class Session(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    start_timestamp = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    end_timestamp = db.Column(db.DateTime)
    attendances = db.relationship('Attendance', backref='session', lazy=True)

class Attendance(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=False)
    session_id = db.Column(db.Integer, db.ForeignKey('session.id'), nullable=False)
    timestamp = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

# Initialize database
def init_db():
    with app.app_context():
        db.create_all()
        
        # Check if admin exists
        admin = Admin.query.filter_by(username='purvesh0207').first()
        if not admin:
            admin = Admin(username='purvesh0207', password='Sayali@0227')
            db.session.add(admin)
            db.session.commit()

init_db()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        admin = Admin.query.filter_by(username=username, password=password).first()
        if admin:
            flask_session['admin_id'] = admin.id
            return redirect(url_for('admin_dashboard'))
        else:
            flash('Invalid credentials')
    return render_template('admin_login.html')

@app.route('/admin/dashboard')
def admin_dashboard():
    if 'admin_id' not in flask_session:
        return redirect(url_for('admin_login'))
    
    active_session = Session.query.filter_by(end_timestamp=None).first()
    return render_template('admin_dashboard.html', active_session=active_session)

@app.route('/admin/create_session', methods=['POST'])
def create_session():
    if 'admin_id' not in flask_session:
        return redirect(url_for('admin_login'))
    
    session_name = request.form.get('session_name')
    
    # End any active sessions
    active_session = Session.query.filter_by(end_timestamp=None).first()
    if active_session:
        active_session.end_timestamp = datetime.utcnow()
        db.session.commit()
    
    # Create new session
    new_session = Session(name=session_name)
    db.session.add(new_session)
    db.session.commit()
    
    flash('Session started successfully!')
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/end_session', methods=['POST'])
def end_session():
    if 'admin_id' not in flask_session:
        return redirect(url_for('admin_login'))
    
    active_session = Session.query.filter_by(end_timestamp=None).first()
    if active_session:
        active_session.end_timestamp = datetime.utcnow()
        db.session.commit()
        flash('Session ended successfully!')
    
    return redirect(url_for('admin_dashboard'))

@app.route('/get_attendance')
def get_attendance():
    if 'admin_id' not in flask_session:
        return jsonify({'success': False, 'message': 'Admin authentication required'})
    
    active_session = Session.query.filter_by(end_timestamp=None).first()
    if not active_session:
        return jsonify({'success': False, 'message': 'No active session', 'attendance': []})
    
    # Get attendance records for current session
    attendance_records = db.session.query(
        Attendance, Student
    ).join(
        Student
    ).filter(
        Attendance.session_id == active_session.id
    ).order_by(
        Attendance.timestamp.desc()
    ).all()
    
    attendance_list = [{
        'roll_number': student.roll_number,
        'name': student.name,
        'time': attendance.timestamp.strftime('%Y-%m-%d %H:%M:%S')
    } for attendance, student in attendance_records]
    
    return jsonify({
        'success': True,
        'attendance': attendance_list
    })

@app.route('/mark_attendance', methods=['POST'])
def mark_attendance():
    if 'admin_id' not in flask_session:
        return jsonify({'success': False, 'message': 'Admin authentication required'})
    
    active_session = Session.query.filter_by(end_timestamp=None).first()
    if not active_session:
        return jsonify({'success': False, 'message': 'No active session'})
    
    qr_data = request.form.get('qr_data')
    if not qr_data:
        return jsonify({'success': False, 'message': 'Invalid QR code data'})
    
    try:
        student_id = int(qr_data)
        student = Student.query.get(student_id)
        
        if not student:
            return jsonify({'success': False, 'message': 'Invalid QR code. Student not found.'})
        
        # Check if attendance already marked
        existing_attendance = Attendance.query.filter_by(
            student_id=student.id,
            session_id=active_session.id
        ).first()
        
        if existing_attendance:
            return jsonify({
                'success': False,
                'message': f'Attendance already marked for {student.name} (Roll: {student.roll_number})',
                'student': {
                    'name': student.name,
                    'roll_number': student.roll_number
                }
            })
        
        # Mark new attendance
        attendance = Attendance(
            student_id=student.id,
            session_id=active_session.id,
            timestamp=datetime.utcnow()
        )
        db.session.add(attendance)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Attendance marked successfully for {student.name} (Roll: {student.roll_number})',
            'student': {
                'name': student.name,
                'roll_number': student.roll_number
            }
        })
        
    except (ValueError, TypeError):
        return jsonify({'success': False, 'message': 'Invalid QR code format'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': 'Failed to mark attendance. Please try again.'})

@app.route('/student/register', methods=['GET', 'POST'])
def student_register():
    if request.method == 'POST':
        name = request.form.get('name')
        roll_number = request.form.get('roll_number')
        college_name = request.form.get('college_name')
        password = request.form.get('password')
        
        # Check if roll number already exists
        existing_student = Student.query.filter_by(roll_number=roll_number).first()
        if existing_student:
            flash('Roll Number already registered')
            return redirect(url_for('student_register'))
        
        # Create new student
        new_student = Student(
            name=name,
            roll_number=roll_number,
            password=password,
            college_name=college_name
        )
        
        try:
            db.session.add(new_student)
            db.session.commit()
            flash('Registration successful! Please login.')
            return redirect(url_for('student_login'))
        except Exception as e:
            db.session.rollback()
            flash('An error occurred during registration')
            return redirect(url_for('student_register'))
    
    return render_template('student_register.html')

@app.route('/student/login', methods=['GET', 'POST'])
def student_login():
    if request.method == 'POST':
        roll_number = request.form.get('roll_number')
        password = request.form.get('password')
        
        student = Student.query.filter_by(roll_number=roll_number).first()
        
        if student and student.password == password:
            flask_session['student_id'] = student.id
            flask_session['student_name'] = student.name
            return redirect(url_for('student_dashboard'))
        else:
            flash('Invalid roll number or password')
            return redirect(url_for('student_login'))
    
    return render_template('student_login.html')

@app.route('/student/dashboard')
def student_dashboard():
    if 'student_id' not in flask_session:
        return redirect(url_for('student_login'))
    
    student = Student.query.get(flask_session['student_id'])
    if not student:
        flask_session.clear()
        return redirect(url_for('student_login'))
    
    # Generate QR code
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(str(student.id))
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    
    # Convert QR code to base64
    buffered = BytesIO()
    img.save(buffered, format="PNG")
    qr_code = base64.b64encode(buffered.getvalue()).decode()
    
    # Get attendance history with session details
    attendance_history = db.session.query(
        Attendance, Session
    ).join(
        Session
    ).filter(
        Attendance.student_id == student.id
    ).order_by(
        Attendance.timestamp.desc()
    ).all()
    
    # Format attendance records
    attendance_records = []
    for attendance, class_session in attendance_history:
        attendance_records.append({
            'date': attendance.timestamp.strftime('%Y-%m-%d'),
            'time': attendance.timestamp.strftime('%H:%M:%S'),
            'session': class_session.name,
            'status': 'Present'
        })
    
    return render_template('student_dashboard.html',
                         student=student,
                         qr_code=qr_code,
                         attendance_history=attendance_records)

@app.route('/admin/logout')
def admin_logout():
    flask_session.pop('admin_id', None)
    return redirect(url_for('admin_login'))

@app.route('/student/logout')
def student_logout():
    flask_session.clear()
    return redirect(url_for('student_login'))

@app.route('/download_attendance')
def download_attendance():
    if 'admin_id' not in flask_session:
        return redirect(url_for('admin_login'))
    
    active_session = Session.query.filter_by(end_timestamp=None).first()
    if not active_session:
        flash('No active session')
        return redirect(url_for('admin_dashboard'))
    
    # Get attendance records
    attendance_records = db.session.query(
        Student.roll_number,
        Student.name,
        Student.college_name,
        Attendance.timestamp
    ).join(
        Attendance, Student.id == Attendance.student_id
    ).filter(
        Attendance.session_id == active_session.id
    ).order_by(
        Student.roll_number
    ).all()
    
    # Create CSV data
    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(['Roll Number', 'Name', 'College', 'Time'])
    
    for record in attendance_records:
        writer.writerow([
            record.roll_number,
            record.name,
            record.college_name,
            record.timestamp.strftime('%Y-%m-%d %H:%M:%S')
        ])
    
    # Create the response
    output.seek(0)
    return Response(
        output,
        mimetype='text/csv',
        headers={
            'Content-Disposition': f'attachment;filename=attendance_{active_session.name}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
        }
    )

@app.route('/download_qr')
def download_qr():
    if 'student_id' not in flask_session:
        return redirect(url_for('student_login'))
    
    student = Student.query.get(flask_session['student_id'])
    if not student:
        return redirect(url_for('student_login'))
    
    # Generate QR code
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(str(student.id))
    qr.make(fit=True)
    
    # Create QR code image
    img = qr.make_image(fill_color="black", back_color="white")
    
    # Save to bytes
    img_io = BytesIO()
    img.save(img_io, 'PNG')
    img_io.seek(0)
    
    return send_file(
        img_io,
        mimetype='image/png',
        as_attachment=True,
        download_name=f'qr_code_{student.roll_number}.png'
    )

if __name__ == '__main__':
    app.run(debug=True)
