from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter

fname = 'sample_resume.pdf'
c = canvas.Canvas(fname, pagesize=letter)
# simple one-page resume
c.setFont('Helvetica-Bold', 14)
c.drawString(100, 750, "John Doe")
c.setFont('Helvetica', 10)
c.drawString(100, 730, "Email: john.doe@example.com")
c.drawString(100, 710, "Experience: 6 years in Python, React, AWS, Docker")
c.drawString(100, 690, "Worked on multiple projects and uses Scrum")
# add additional skills line
c.drawString(100, 670, "Skills: Python, React, AWS, Docker, Kubernetes, SQL")
c.save()
print('created', fname)
