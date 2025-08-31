import os
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
import json

class PDFQuoteGenerator:
    def __init__(self):
        self.styles = getSampleStyleSheet()
        self.setup_custom_styles()
    
    def setup_custom_styles(self):
        # Custom styles for professional look
        self.styles.add(ParagraphStyle(
            name='CompanyHeader',
            parent=self.styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#2c3e50'),
            alignment=TA_CENTER,
            spaceAfter=20
        ))
        
        self.styles.add(ParagraphStyle(
            name='QuoteTitle',
            parent=self.styles['Heading2'],
            fontSize=18,
            textColor=colors.HexColor('#3498db'),
            alignment=TA_CENTER,
            spaceAfter=15
        ))
        
        self.styles.add(ParagraphStyle(
            name='SectionHeader',
            parent=self.styles['Heading3'],
            fontSize=14,
            textColor=colors.HexColor('#2c3e50'),
            spaceBefore=15,
            spaceAfter=10
        ))

    def generate_quote_pdf(self, quote, customer, filename):
        """Generate a professional PDF quote"""
        try:
            # Create the PDF document
            doc = SimpleDocTemplate(filename, pagesize=letter)
            story = []
            
            # Company Header with Logo
            if os.path.exists('static/images/dtf-logo.png'):
                logo = Image('static/images/dtf-logo.png', width=2*inch, height=1*inch)
                logo.hAlign = 'CENTER'
                story.append(logo)
                story.append(Spacer(1, 20))
            
            # Company Name
            story.append(Paragraph("DTF DESIGNS", self.styles['CompanyHeader']))
            story.append(Paragraph("Professional Print Solutions", self.styles['Normal']))
            story.append(Spacer(1, 30))
            
            # Quote Title
            story.append(Paragraph(f"QUOTE #{quote.quote_number}", self.styles['QuoteTitle']))
            story.append(Spacer(1, 20))
            
            # Customer & Quote Info Section
            info_data = [
                ['QUOTE INFORMATION', ''],
                ['Quote Date:', datetime.now().strftime('%B %d, %Y')],
                ['Quote Number:', quote.quote_number],
                ['Status:', quote.status.title()],
                ['Expires:', quote.expires_at.strftime('%B %d, %Y') if quote.expires_at else 'N/A'],
                ['', ''],
                ['CUSTOMER INFORMATION', ''],
                ['Name:', customer.name],
                ['Email:', customer.email],
                ['Phone:', customer.phone or 'N/A'],
                ['Company:', customer.company or 'N/A'],
            ]
            
            info_table = Table(info_data, colWidths=[2*inch, 4*inch])
            info_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (1, 0), colors.HexColor('#3498db')),
                ('TEXTCOLOR', (0, 0), (1, 0), colors.whitesmoke),
                ('BACKGROUND', (0, 6), (1, 6), colors.HexColor('#3498db')),
                ('TEXTCOLOR', (0, 6), (1, 6), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('FONTNAME', (0, 0), (1, 0), 'Helvetica-Bold'),
                ('FONTNAME', (0, 6), (1, 6), 'Helvetica-Bold'),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            
            story.append(info_table)
            story.append(Spacer(1, 30))
            
            # Product Details Section
            story.append(Paragraph("PROJECT DETAILS", self.styles['SectionHeader']))
            
            product_details = quote.product_details
            if isinstance(product_details, str):
                product_details = json.loads(product_details)
            
            # Create product details table
            details_data = [['Item', 'Specification']]
            details_data.append(['Category', quote.category.title()])
            
            for key, value in product_details.items():
                if key not in ['csrf_token'] and value:
                    clean_key = key.replace('_', ' ').title()
                    details_data.append([clean_key, str(value)])
            
            details_table = Table(details_data, colWidths=[2*inch, 4*inch])
            details_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#34495e')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('VALIGN', (0, 0), (-1, -1), 'TOP')
            ]))
            
            story.append(details_table)
            story.append(Spacer(1, 30))
            
            # Cost Breakdown Section
            story.append(Paragraph("COST BREAKDOWN", self.styles['SectionHeader']))
            
            cost_breakdown = quote.cost_breakdown
            if isinstance(cost_breakdown, str):
                cost_breakdown = json.loads(cost_breakdown)
            
            cost_data = [['Description', 'Amount']]
            
            if cost_breakdown:
                for key, value in cost_breakdown.items():
                    if key != 'total' and value > 0:
                        clean_key = key.replace('_', ' ').title()
                        cost_data.append([clean_key, f"${value:.2f}"])
            
            # Add admin adjustments if any
            if quote.admin_adjustments and quote.admin_adjustments != 0:
                cost_data.append(['Admin Adjustment', f"${quote.admin_adjustments:.2f}"])
            
            # Final price
            final_price = quote.final_price if quote.final_price else quote.calculated_price
            cost_data.append(['', ''])
            cost_data.append(['TOTAL PRICE', f"${final_price:.2f}"])
            
            cost_table = Table(cost_data, colWidths=[4*inch, 2*inch])
            cost_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#27ae60')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#2ecc71')),
                ('TEXTCOLOR', (0, -1), (-1, -1), colors.whitesmoke),
                ('ALIGN', (0, 0), (0, -1), 'LEFT'),
                ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
                ('FONTSIZE', (0, -1), (-1, -1), 12),
                ('FONTNAME', (0, 1), (-1, -2), 'Helvetica'),
                ('FONTSIZE', (0, 0), (-1, -2), 10),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            
            story.append(cost_table)
            story.append(Spacer(1, 30))
            
            # Terms and Conditions
            story.append(Paragraph("TERMS & CONDITIONS", self.styles['SectionHeader']))
            terms = """
            • This quote is valid for 30 days from the date issued<br/>
            • 50% deposit required to begin production<br/>
            • Balance due upon completion<br/>
            • Production time: 3-5 business days (standard), 1-2 days (rush)<br/>
            • Customer approval required before production begins<br/>
            • DTF Designs is not responsible for spelling errors in customer-provided text<br/>
            • All sales are final once production has begun
            """
            story.append(Paragraph(terms, self.styles['Normal']))
            story.append(Spacer(1, 20))
            
            # Footer
            footer_text = f"""
            <para align=center>
            Thank you for choosing DTF Designs!<br/>
            Questions? Contact us at info@dtfdesigns.com or (555) 123-4567<br/>
            <b>Ready to move forward? Reply to approve this quote!</b>
            </para>
            """
            story.append(Paragraph(footer_text, self.styles['Normal']))
            
            # Build the PDF
            doc.build(story)
            
            return True, "PDF generated successfully"
            
        except Exception as e:
            return False, f"Error generating PDF: {str(e)}"

    def generate_invoice_pdf(self, order, customer, filename):
        """Generate a professional invoice PDF"""
        # Similar structure but with invoice-specific formatting
        # This would be implemented similarly to quote PDF
        pass