from app import app, db, Admin

def init_db():
    with app.app_context():
        # Create all tables
        db.drop_all()
        db.create_all()
        
        # Create admin user
        admin = Admin(username='purvesh0207', password='Sayali@0227')
        db.session.add(admin)
        db.session.commit()

if __name__ == '__main__':
    init_db()
    print("Database initialized successfully!")
