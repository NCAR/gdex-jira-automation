from reportlab.pdfgen import canvas
from io import BytesIO
from datetime import datetime, timezone
import requests
from PyPDF2 import PdfReader, PdfWriter

def download_pdf(url, filename):
    response = requests.get(url)
    with open(filename, "wb") as f:
        f.write(response.content)


def create_ack_overlay(name, email):
    packet = BytesIO()
    c = canvas.Canvas(packet)

    # Use UTC timestamp
    date = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

    # Position at bottom of page (x=50, y=40)
    c.setFont("Helvetica", 10)
    c.drawString(50, 40, f"Acknowledged by: {name} ({email})")
    c.drawString(50, 25, f"Date: {date}")

    c.save()
    packet.seek(0)
    return packet


def add_acknowledgment(input_pdf_path, name, email):
    reader = PdfReader(input_pdf_path)
    writer = PdfWriter()

    overlay_pdf = PdfReader(create_ack_overlay(name, email))
    overlay_page = overlay_pdf.pages[0]

    for page in reader.pages:
        page.merge_page(overlay_page)
        writer.add_page(page)

    output = BytesIO()
    writer.write(output)
    output.seek(0)
    return output

def generate_dda_response(jira_instance, ticket_details):
    if ticket_details.get("lab") != "External":
        return

    url = "https://gdex.ucar.edu/documents/57/gdex_dda.pdf"
    filename = "gdex_dda.pdf"
    download_pdf(url, filename)

    ticket_id = ticket_details['key']
    reporter_email = ticket_details['reporter_email']
    full_name = ticket_details['reporter_name']
    name = full_name.lower().replace(" ", "_")
    date = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    attachment_filename = f"{name}_{date}.pdf"
    pdf_buffer = add_acknowledgment(filename, full_name, reporter_email)
    jira_instance.jira.add_attachment(issue=ticket_id, attachment=pdf_buffer, filename=attachment_filename)

    comment = (
        f"Thank you, {full_name}. We have received your acknowledgment of the "
        f"[GDEX Data Deposit Agreement|https://gdex.ucar.edu/documents/57/gdex_dda.pdf]. "
        f"A signed copy has been attached to this ticket for your records: [^{attachment_filename}]"
    )
    jira_instance.add_comment_to_ticket(ticket_id, comment)



