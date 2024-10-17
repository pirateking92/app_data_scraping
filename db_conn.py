import logging
import psycopg2

# Database connection details
DB_HOST = "127.0.0.1"
DB_NAME = "datamigrationmakers"
DB_USER = "mattdoyle"
DB_PASS = ""

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class db_conn:
    def connect_to_database(self):
        """Connects to the PostgreSQL database."""
        try:
            conn = psycopg2.connect(
                host=DB_HOST, database=DB_NAME, user=DB_USER, password=DB_PASS
            )
            logger.info("Connected to the database.")
            return conn
        except Exception as e:
            logger.error(f"Database connection failed: {str(e)}")
            return None
