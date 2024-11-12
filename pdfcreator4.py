from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas
from reportlab.platypus import Paragraph
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase.pdfmetrics import stringWidth
from PIL import Image, ImageDraw, ImageOps
from io import BytesIO
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import os
import requests
import math
from reportlab.lib import colors
from reportlab.lib.units import inch

def create_gradient_background(c, x, width, height):
    """Create a subtle two-tone gradient background."""
    c.saveState()
    
    # Define the start and end colors for the gradient
    start_color = colors.HexColor('#2C3E50')  # Deep navy blue
    end_color = colors.HexColor('#4CA1AF')    # Lighter blue
    
    # Number of gradient steps
    steps = 100
    step_height = height / steps
    
    for i in range(steps):
        # Calculate interpolation factor
        t = i / float(steps - 1)
        
        # Interpolate between start and end colors
        r = start_color.red + t * (end_color.red - start_color.red)
        g = start_color.green + t * (end_color.green - start_color.green)
        b = start_color.blue + t * (end_color.blue - start_color.blue)
        
        # Set the fill color
        c.setFillColorRGB(r, g, b)
        
        # Draw the rectangle strip
        y = height - (i + 1) * step_height
        c.rect(x, y, width, step_height, fill=1, stroke=0)
    
    c.restoreState()

def create_hexagonal_image(image_path, size):
    """Create a hexagonal profile image"""
    img = Image.open(image_path)
    
    # Create mask
    mask = Image.new('L', (size, size), 0)
    draw = ImageDraw.Draw(mask)
    
    # Calculate hexagon points
    center = size // 2
    edge = size // 3
    points = [
        (center, 0),
        (center + edge, edge),
        (center + edge, size - edge),
        (center, size),
        (center - edge, size - edge),
        (center - edge, edge)
    ]
    draw.polygon(points, fill=255)
    
    # Resize and crop image
    img = ImageOps.fit(img, (size, size), method=Image.Resampling.LANCZOS)
    output = Image.new('RGBA', (size, size), (255, 255, 255, 0))
    output.paste(img, (0, 0))
    output.putalpha(mask)
    
    return output
def setup_font_awesome():
    font_path = 'fontawesome-webfont.ttf'
    if not os.path.exists(font_path):
        print("Downloading FontAwesome...")
        url = "https://cdnjs.cloudflare.com/ajax/libs/font-awesome/4.7.0/fonts/fontawesome-webfont.ttf"
        response = requests.get(url)
        with open(font_path, 'wb') as f:
            f.write(response.content)
    
    # Register the font
    pdfmetrics.registerFont(TTFont('FontAwesome', font_path))

def create_cv(filename, data, image_path):
    c = canvas.Canvas(filename, pagesize=letter)
    width, height = letter
   # Setup FontAwesome
    setup_font_awesome()
    
    c = canvas.Canvas(filename, pagesize=letter)
    width, height = letter
    # Create gradient background
    create_gradient_background(c, 0, 3*inch, height)

    # Add hexagonal profile image
    hex_size = int(1.5 * inch)
    hex_image = create_hexagonal_image(image_path, hex_size * 2)
    img_buffer = BytesIO()
    hex_image.save(img_buffer, format='PNG')
    img_buffer.seek(0)
    
    c.drawImage(ImageReader(img_buffer), 
                0.75*inch,
                height - 2*inch,
                width=hex_size,
                height=hex_size,
                mask='auto')

    # Header section
    c.setFillColor(colors.HexColor('#2C3E50'))
    c.setFont('Helvetica-Bold', 24)
    c.drawString(3.2*inch, height - 1*inch, data['name'])
    
    c.setFont('Helvetica', 16)
    c.setFillColor(colors.HexColor('#1976D2'))
    c.drawString(3.2*inch, height - 1.4*inch, data['title'])

    # Contact information with icons and links
    contact_info = [
        ('\uf0e0', data['email']),               # Email
        ('\uf095', data['phone']),               # Phone
        ('\uf124', data['location']),            # Location
        ('\uf08c', 'LinkedIn', data['social_links']['linkedin']),   # LinkedIn
        ('\uf09b', 'GitHub', data['social_links']['github'])        # GitHub
    ]
    
    y_start = height - 0.7*inch
    for item in contact_info:
        # Determine if item has a link
        if len(item) == 3:  # items with links (LinkedIn and GitHub)
            icon, text, link = item
        else:  # items without links
            icon, text = item
            link = ''
            
        # Calculate text width for right alignment
        text_width = stringWidth(text, 'Helvetica', 10)
        icon_width = stringWidth(icon, 'FontAwesome', 12)
        total_width = icon_width + 10 + text_width  # 10 is spacing between icon and text
        
        c.setFillColor(colors.HexColor('#2C3E50'))
        
        # Draw the icon with FontAwesome - right aligned
        c.setFont('FontAwesome', 12)
        icon_x = width - 0.5*inch - total_width  # Start from right margin
        c.drawString(icon_x, y_start, icon)
        
        # Draw the text with Helvetica - right aligned
        c.setFont('Helvetica', 10)
        text_x = icon_x + icon_width + 10  # Position text after icon
        c.drawString(text_x, y_start, text)
        
        # Add clickable link only for LinkedIn and GitHub
        if len(item) == 3:  # Only for items with links
            rect = (text_x, y_start - 2,
                   text_x + text_width, y_start + 10)
            c.linkURL(link, rect, relative=0, thickness=0)
            
            # Add subtle underline only for linked items
            c.setStrokeColor(colors.HexColor('#1976D2'))
            c.setLineWidth(0.5)
            c.line(text_x, y_start - 1,
                   text_x + text_width, y_start - 1)
        
        y_start -= 0.25*inch

    # Left column sections
    y = height - 2.5*inch
    for section in ['Technical Skills', 'Education', 'Certifications', 'Languages']:
        c.setFillColor(colors.white)
        c.setFont('Helvetica-Bold', 14)
        c.drawString(0.5*inch, y, section)
        y -= 0.4*inch
        
        c.setFont('Helvetica', 10)
        for item in data[section.lower().replace(' ', '_')]:
            c.drawString(0.7*inch, y, f"• {item}")
            y -= 0.25*inch
        y -= 0.3*inch

    # Experience section
    y = height - 2.5*inch
    c.setFillColor(colors.HexColor('#1976D2'))
    c.setFont('Helvetica-Bold', 16)
    c.drawString(3.2*inch, height - 2*inch, "Professional Experience")

    for job in data['experience']:
        # Company name with link
        c.setFillColor(colors.HexColor('#1976D2'))
        c.setFont('Helvetica-Bold', 11)
        company_text = job['company']
        company_width = stringWidth(company_text, 'Helvetica-Bold', 14)
        c.drawString(3.2*inch, y, company_text)
        
        # Add company website link if available
        if 'company_url' in job:
            rect = (3.2*inch, y - 2,
                   3.2*inch + company_width, y + 12)
            c.linkURL(job['company_url'], rect, relative=0, thickness=0)
            
            # Add subtle underline for company links
            c.setStrokeColor(colors.HexColor('#1976D2'))
            c.setLineWidth(0.5)
            c.line(3.2*inch, y - 1,
                   3.2*inch + company_width, y - 1)
        
       # Job details with a slightly smaller font size
        y -= 0.3 * inch
        c.setFillColor(colors.HexColor('#2C3E50'))  # Dark blue color
        c.setFont('Helvetica-Bold', 7)  # Adjusting job title font size only
        c.setFont('Helvetica-Bold', 12)
        c.drawString(3.2*inch, y, job['title'])
        # Draw job title, location, and dates in one line
        c.drawString(3.2 * inch, y, f"{job['title']} | {job['location']} | {job['dates']}")

        # Description bullets with reduced font size only
        y -= 0.3 * inch  # Reduced spacing above bullet points
        for bullet in job['description']:
            text = Paragraph(
                f"• {bullet}",
                ParagraphStyle(
                    'bullet',
                    fontName='Helvetica',
                    fontSize=8,  # Set smaller font size for bullet points
                    leftIndent=20,
                )
            )
            text_width, text_height = text.wrap(4.5 * inch, height)
            text.drawOn(c, 3.4 * inch, y - text_height)
            y -= text_height + 0.1 * inch  # Slight spacing reduction between bullets
        y -= 0.2 * inch  # Standard spacing after job description

    c.save()

# Updated CV data with social links and company URLs
cv_data = {
    'name': 'Faris Alahmad',
    'title': 'Software Developer',
    'email': 'Farisalahmad714@gmail.com',
    'phone': '(714)-386-2366',
    'location': 'Anaheim, CA 92801',
    'social_links': {
        'linkedin': 'https://www.linkedin.com/in/farisahmad1/',  # Add your LinkedIn URL
        'github': 'https://github.com/FarisAlahmad714'  # Add your GitHub URL
    },
    'technical_skills': [
        'Management', 'Client Relations', 'Customer Service', 
        'Software Development', 'Sales Expert', 'Social Media Marketeer',
        'Prompt Engineering', 'Data Analysis', 'Financial Services',
        'Credit Analysis', 'Database Management'
    ],
    'education': ['Cypress College', 'Coding Dojo'],
    'certifications': ['Full Stack Developer', 'NMLS', 'Sales License'],
    'languages': ['English', 'Arabic'],
    'experience': [
        {
            'company': 'Ennkar',
            'company_url': 'https://www.ennkar.com',
            'title': 'Loan Officer',
            'location': 'Orange',
            'dates': '04/2020 - 06/2023',
            'description': [
                'Operated in a high-pressure sales environment specializing in reverse mortgages for seniors aged 62+',
                'Educated clients on loan refinancing options, maintaining a patient and informative approach despite remote work challenges due to COVID-19.',
                'Conducted primarily phone-based business during COVID, demonstrating patience to achieve success.'
            ]
        },
        {
            'company': 'BMW of Buena Park',
            'company_url': 'https://www.bmwbuenapark.com',
            'title': 'Client Advisor',
            'location': 'Buena Park',
            'dates': '11/2018 - 12/2019',
            'description': [
                'Provided expert guidance to customers in selecting vehicles, leveraging knowledge of the automotive market from previous experience to enhance customer satisfaction.',
                'Successfully achieved a high rate of sales conversions through personalized service and effective communication, resulting in a monthly sales increase averaging 17-20% over the year.',
                'Collaborated with the sales team to exceed monthly sales goals, contributing to overall dealership success.'
            ]
        },
        {
            'company': 'Autonation Toyota Buena Park',
            'company_url': 'https://www.autonation.com',
            'title': 'Sales Consultant',
            'location': 'Buena Park',
            'dates': '11/2017 - 10/2018',
            'description': [
                'Assisted customers in finding the right new or used vehicles, resulting in an average 10-15% increase month-to-month sales in the duration of a year.',
                'Established enduring relationships with clients, effectively securing their loyalty after successful conversions & retained this valuable client base through seamless transitions between different dealerships.',
                'Worked effectively across both floor sales and the eCommerce department, consistently meeting sales targets.'
            ]
        },
        {
            'company': 'AlMokhtar Hookah Lounge',
            'title': 'Manager & Server',
            'location': 'Anaheim',
            'dates': '07/2014 - 05/2018',
            'description': [
                'Maintained a safe working environment for the workforce of 2-3 employees, managed the operations from finances to event planning, and social media marketing',
                'Ensured customer satisfaction at a maximum, which continually led to plenty of returning customers and a well-performing business overall.',
                'Successfully grew the family business through effective management strategies and customer engagement.'
            ]
        }
    ]
}

# Create the CV
image_path = 'me1.jpg'  # Replace with your actual image path
create_cv('high_quality_cv2.pdf', cv_data, image_path)