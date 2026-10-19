import os
from fpdf import FPDF
from tools import register_tool

@register_tool(name="generate_pdf_report", description="توليد تقرير PDF منظم ومصمم للعميل.")
def generate_pdf_report(
    title: str = "Client Qualification Report", 
    content: str = "Default content.", 
    filename: str = "summary_report.pdf",
    **kwargs  # التقاط أي وسائط إضافية يمررها النموذج بالخطأ لمنع تعطل النظام
) -> str:
    """
    يقوم بإنشاء ملف PDF بناءً على التقرير المستخرج.
    يرجع نصاً يبدأ بـ 'SUCCESS' في حال نجاح العملية ليتعرف عليه البوت.
    """
    try:
        pdf = FPDF()
        pdf.add_page()
        
        # إضافة العنوان
        pdf.set_font("Arial", 'B', 16)
        pdf.cell(0, 10, title, ln=True, align='C')
        pdf.ln(10)
        
        # إضافة المحتوى
        pdf.set_font("Arial", size=12)
        pdf.multi_cell(0, 8, content)
        
        # حفظ الملف
        pdf.output(filename)
        
        if os.path.exists(filename):
            return f"SUCCESS: PDF report generated as '{filename}'"
        else:
            return "Error: File was not created."
            
    except Exception as e:
        return f"Error generating PDF report: {str(e)}"