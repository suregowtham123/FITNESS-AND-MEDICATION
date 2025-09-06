from app import app, db, Doctor  # import app along with db

# Use application context
with app.app_context():
    # Create tables
    db.create_all()

    # Add sample doctors if none exist
    if not Doctor.query.first():
        doc1 = Doctor(name="Dr. Smith", available=True)
        doc2 = Doctor(name="Dr. Jane", available=False)
        db.session.add_all([doc1, doc2])
        db.session.commit()

    print("Database initialized and sample doctors added.")
