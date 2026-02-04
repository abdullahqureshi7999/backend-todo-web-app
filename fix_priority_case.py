"""
Migration script to fix priority enum case mismatch.
Converts all uppercase priority values (NONE, LOW, MEDIUM, HIGH) to lowercase (none, low, medium, high).
"""
from sqlmodel import Session, create_engine, text
from src.config import settings

def fix_priority_case():
    """Update all priority values to lowercase"""
    engine = create_engine(settings.database_url)

    with Session(engine) as session:
        # Update all uppercase priority values to lowercase
        updates = [
            ("NONE", "none"),
            ("LOW", "low"),
            ("MEDIUM", "medium"),
            ("HIGH", "high"),
        ]

        for old_value, new_value in updates:
            statement = text("UPDATE task SET priority = :new_value WHERE priority = :old_value")
            result = session.execute(statement, {"old_value": old_value, "new_value": new_value})
            count = result.rowcount
            if count > 0:
                print(f"Updated {count} tasks from '{old_value}' to '{new_value}'")

        session.commit()
        print("✓ Priority case migration completed successfully")

if __name__ == "__main__":
    print("Starting priority case migration...")
    fix_priority_case()
