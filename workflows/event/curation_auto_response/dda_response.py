from reportlab.pdfgen import canvas
from io import BytesIO
from datetime import datetime, timezone
import requests
from PyPDF2 import PdfReader, PdfWriter

def download_pdf(url, filename):
    response = requests.get(url)
    with open(filename, "wb") as f:
        f.write(response.content)


def create_ack_overlay(email):
    packet = BytesIO()
    c = canvas.Canvas(packet)

    # Use UTC timestamp
    date = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

    # Position at bottom of page (x=50, y=40)
    c.setFont("Helvetica", 10)
    c.drawString(50, 40, f"Acknowledged by: {email}")
    c.drawString(50, 25, f"Date: {date}")

    c.save()
    packet.seek(0)
    return packet


def add_acknowledgment(input_pdf_path, output_pdf_path, email):
    # Read original PDF
    reader = PdfReader(input_pdf_path)
    writer = PdfWriter()

    # Create overlay in memory
    overlay_pdf = PdfReader(create_ack_overlay(email))
    overlay_page = overlay_pdf.pages[0] 
    # Loop through all pages of the original PDF
    for page in reader.pages:
        # Merge the same overlay on every page
        page.merge_page(overlay_page)
        writer.add_page(page)

    # Write final PDF
    with open(output_pdf_path, "wb") as f:
        writer.write(f)

def main():
    # Example usage
    url = "https://gdex.ucar.edu/documents/57/gdex_dda.pdf"
    filename = "gdex_dda.pdf"
    download_pdf(url, filename)

    First = "Calie"
    Last = "Payne"
    full_name = f"{First} {Last}"
    email = "caliepayne@ucar.edu"
    date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    add_acknowledgment(filename, f"{Last}_{date}.pdf", email)
if __name__ == "__main__":
    main()
