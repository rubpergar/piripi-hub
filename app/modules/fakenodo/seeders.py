from app import db
from app.modules.fakenodo.models import Deposition


def seed_depositions():
    """Seeds the Deposition table with sample data."""
    if Deposition.query.count() == 0:
        print("Seeding the Deposition table...")

        depositions = [
            Deposition(
                dep_metadata={"title": "Sample Dataset 1", "description": "Description for dataset 1"},
                status="draft",
                doi=None
            ),
            Deposition(
                dep_metadata={"title": "Sample Dataset 2", "description": "Description for dataset 2"},
                status="published",
                doi="fakenodo.doi.2"
            ),
            Deposition(
                dep_metadata={"title": "Sample Dataset 3", "description": "Description for dataset 3"},
                status="draft",
                doi="fakenodo.doi.3"
            ),
        ]

        db.session.bulk_save_objects(depositions)
        db.session.commit()
        print("Deposition table seeded successfully.")
    else:
        print("Deposition table already contains data. Skipping seeding.")