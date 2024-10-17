import logging
from weasyprint import HTML

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class html_to_pdf:
    def convert_html_file_to_pdf(filename):
        """Convert an HTML file to PDF if applicable."""
        if filename.endswith(".html"):
            pdf_filename = filename.replace(".html", ".pdf")
            try:
                HTML(filename).write_pdf(pdf_filename)
                logger.info(f"Successfully converted {filename} to PDF.")
                return pdf_filename
            except Exception as e:
                logger.error(f"Failed to convert {filename} to PDF: {str(e)}")
                return None
        return None
