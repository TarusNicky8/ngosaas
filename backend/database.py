        # backend/database.py

        from sqlalchemy import create_engine
        from sqlalchemy.ext.declarative import declarative_base
        from sqlalchemy.orm import sessionmaker
        import os

        # For Render deployment, DATABASE_URL MUST come from environment variables.
        # There should be NO local file fallback when deploying.
        DATABASE_URL = os.environ.get("DATABASE_URL")

        if DATABASE_URL is None:
            # In a deployed environment, this indicates a missing configuration.
            # During local development, you might set this via a .env file or directly in your shell.
            print("WARNING: DATABASE_URL environment variable is not set. Database connection will likely fail.")
            # Raise an error to prevent server startup without a database connection in production.
            # For development, you might choose to default to SQLite here, but not for deployment.
            raise Exception("DATABASE_URL environment variable is required for database connection.")


        # Configure connect_args based on the database type.
        # The 'check_same_thread' argument is specific to SQLite and is not needed for PostgreSQL.
        connect_args = {}
        # If you were supporting SQLite locally, you'd add this condition.
        # For pure PostgreSQL deployment, this can be omitted.
        # if "sqlite" in DATABASE_URL:
        #     connect_args["check_same_thread"] = False


        engine = create_engine(
            DATABASE_URL,
            connect_args=connect_args, # Only relevant if connect_args are added (e.g., for SQLite)
            echo=False
        )

        SessionLocal = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=engine
        )

        Base = declarative_base()
        