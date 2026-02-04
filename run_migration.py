"""
Run database migration for 002-todo-organization-features.

This script executes the SQL migration to add priority and tags support.
"""
from sqlalchemy import text
from src.db.database import engine


def run_migration():
    """Execute the 002 migration SQL"""
    migration_file = "migrations/002_add_priority_and_tags.sql"

    print(f"Running migration: {migration_file}")

    # Read migration SQL
    with open(migration_file, "r", encoding="utf-8") as f:
        migration_sql = f.read()

    # Remove comments and split by semicolons
    lines = []
    for line in migration_sql.split("\n"):
        # Skip comment lines
        if line.strip().startswith("--"):
            continue
        lines.append(line)

    cleaned_sql = "\n".join(lines)
    statements = [s.strip() for s in cleaned_sql.split(";") if s.strip()]

    with engine.connect() as conn:
        for i, statement in enumerate(statements, 1):
            if not statement:
                continue
            print(f"Executing statement {i}/{len(statements)}...")
            print(f"  SQL: {statement[:60]}...")
            try:
                conn.execute(text(statement))
                conn.commit()
                print(f"  [OK] Statement {i} completed")
            except Exception as e:
                # Check if error is "already exists" which we can ignore
                error_msg = str(e).lower()
                if "already exists" in error_msg or "duplicate" in error_msg:
                    print(f"  [SKIP] Statement {i} already applied")
                    conn.rollback()
                else:
                    print(f"  [FAIL] Statement {i} failed: {e}")
                    conn.rollback()
                    raise

    print("\n[SUCCESS] Migration completed successfully!")


if __name__ == "__main__":
    run_migration()
