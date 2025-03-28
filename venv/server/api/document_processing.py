import io
import fitz  # PyMuPDF
import tabula  # Tabula-py for extracting tables

def extract_text_from_pdf(file_stream):
    """
    Extracts text from a PDF file provided as a file-like object.

    Args:
        file_stream (file-like object): The uploaded PDF file stream.

    Returns:
        str: The complete extracted text from the PDF.
    """
    # Open the PDF in memory using PyMuPDF
    doc = fitz.open(stream=file_stream.read(), filetype="pdf")
    full_text = ""

    # Iterate over each page and extract text
    for page in doc:
        full_text += page.get_text()

    return full_text


def extract_tables_from_pdf(pdf_path):
    """
    Extracts tables from a local PDF file using Tabula-py.

    Args:
        pdf_path (str): The path to the local PDF file.

    Returns:
        list: A list of DataFrame objects representing the tables.
    """
    try:
        # Use Tabula to read all tables from the PDF
        tables = tabula.read_pdf(pdf_path, pages='all', multiple_tables=True)
        return tables
    except Exception as e:
        # Print error message if table extraction fails
        print(f"Error processing PDF tables: {str(e)}")
        return None
