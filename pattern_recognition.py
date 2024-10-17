import logging
import re
from db_conn import db_conn

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class Pattern_Recog:
    def get_learner_name(self, uuid):
        """Fetches the learner's full name from the database based on UUID."""
        conn = db_conn.connect_to_database(self)
        if conn is None:
            return None

        try:
            with conn.cursor() as cursor:
                cursor.execute(
                    "SELECT learner_full_name FROM apprentice_info WHERE ApplicationId = %s",
                    (uuid.upper(),),
                )
                result = cursor.fetchone()
                return result[0] if result else None
        except Exception as e:
            logger.error(f"Failed to fetch learner name for UUID {uuid}: {str(e)}")
            return None
        finally:
            conn.close()

    def remove_unique_identifier(self, filename):
        """Removes unique identifiers (UUIDs, timestamps, etc.) from filenames and reformats."""
        logger.info(f"Processing filename: {filename}")

        patterns = [
            r"^([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})\."
            r"([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})\."
            r"(\d{8}T\d{6}-\d{3}Z)\.([\w\s\[\]\-().,'&+–!]+)\.(\w+)$",
            r"^([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})\."
            r"([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})\."
            r"(\d{8}T\d{6}-\d{3}Z)\.([\w\s\[\]\-().,'&_!]+)\.(.*)$",
            r"^([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})\."
            r"([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})\."
            r"(\d{8}T\d{5}-\d{3}Z)\.([\w\s\[\]\-().,'&_+!]+)\.([a-zA-Z0-9]+)$",
            r"^([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})\."
            r"([a-zA-Z0-9]+)\.\d{8}T\d{6}-\d{3}Z(\.[a-zA-Z0-9]+)$",
            r"^([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})\."
            r"([a-zA-Z0-9]+)\.\d{8}T\d{6}-\d{3}Z\.(.*?)\.(.*)$",
            r"^([a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12})\."
            r"([a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12})\."
            r"(\d{8}T\d{6}-\d{3}Z\.[\w\s\[\]\-().,'&_!]+\.[a-zA-Z0-9]+)$",
            r"^([a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12})\."
            r"([a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12})\."
            r"\d{8}T([0-9]{6}|[7-9][0-9]{4})-\d{3}Z\.[\w\s\[\]\-().,'&_!+]+(\.[a-zA-Z0-9]+)+$",
            r"^[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}\."
            r"[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}\."
            r"\d{8}T\d{5}-\d{3}Z\.[\w\s\[\]\-().,'&_+*!]+(\.[a-zA-Z0-9]+)+$",
            # Corrected pattern with additional group for text between the timestamp and file extension
            r"^([a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12})\."
            r"([a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12})\."
            r"(\d{8}T\d{5}-\d{3}Z)\.([\w\s\[\]\-().,'&_+!]+)\.([a-zA-Z0-9]+)$",
        ]

        for pattern in patterns:
            match = re.match(pattern, filename)
            if match:
                logger.debug(f"Pattern matched: {pattern}")
                logger.debug(f"Captured Groups: {match.groups()}")

                uuid = match.group(1)
                time_stamp = match.group(3) if len(match.groups()) > 2 else ""
                description = match.group(4) if match.lastindex >= 4 else ""
                file_extension = match.group(match.lastindex)
                remaining_part = time_stamp.rstrip()

                # Validate UUID length
                if uuid and len(uuid) == 36:
                    learner_name = self.get_learner_name(uuid)
                else:
                    logger.warning(
                        "Invalid UUID found in filename. Skipping learner name lookup."
                    )
                    learner_name = None

                if learner_name:
                    if remaining_part:
                        new_filename = f"{learner_name} - {remaining_part[0:8]} - {description}.{file_extension}"
                    else:
                        new_filename = (
                            f"{learner_name} - {description}.{file_extension}"
                        )

                    return new_filename.rstrip(), filename.endswith(".html")
                else:
                    logger.warning(
                        f"No learner name found for UUID {uuid}. Using original filename."
                    )
                    return filename, filename.endswith(".html")

        logger.info("No patterns matched. No changes made.")
        return filename, False
