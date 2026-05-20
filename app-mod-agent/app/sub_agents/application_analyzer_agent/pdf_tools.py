import logging
import io
import re
import base64
import requests
from google.adk.tools import ToolContext
from google.genai.types import Part, Blob
from markdown_pdf import MarkdownPdf, Section

def process_mermaid(markdown_text: str) -> str:
    """
    Finds Mermaid blocks in markdown, fetches rendered images from mermaid.ink,
    and replaces blocks with data URI images.
    """
    logging.info("Processing Mermaid diagrams...")
    pattern = re.compile(r"```mermaid\n(.*?)\n```", re.DOTALL)
    matches = pattern.findall(markdown_text)
    
    processed_text = markdown_text
    for i, match in enumerate(matches):
        code = match.strip()
        # Encode to base64
        encoded = base64.b64encode(code.encode('utf-8')).decode('utf-8')
        url = f"https://mermaid.ink/img/{encoded}"
        
        try:
            logging.info("Fetching Mermaid image from %s", url)
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                # Convert to data URI
                img_base64 = base64.b64encode(response.content).decode('utf-8')
                data_uri = f"data:image/png;base64,{img_base64}"
                # Replace in markdown
                processed_text = processed_text.replace(f"```mermaid\n{match}\n```", f"![Mermaid Diagram]({data_uri})")
                logging.info("Successfully replaced Mermaid block %d with image.", i+1)
            else:
                logging.warning("Failed to fetch Mermaid image from %s: %d", url, response.status_code)
        except Exception as e:
            logging.warning("Error fetching Mermaid image: %s", e)
            
    return processed_text

async def convert_report_to_pdf(report_content: str, tool_context: ToolContext) -> bool:
    """
    Converts a markdown report into a PDF report and saves it as an artifact.
    """
    logging.info("Converting markdown report to PDF...")
    
    try:
        # 1. Preprocess Mermaid diagrams
        processed_report = process_mermaid(report_content)
        
        # 2. Create PDF and add section with CSS
        pdf = MarkdownPdf(toc_level=0)
        
        # Google-inspired CSS
        google_css = """
        @import url('https://fonts.googleapis.com/css2?family=Google+Sans:wght@400;500;700&family=Roboto:wght@400;500;700&display=swap');
        * {
            box-sizing: border-box;
            font-family: 'Google Sans', 'Roboto', 'Arial', sans-serif;
        }
        body {
            line-height: 1.6;
            color: #3c4043;
            margin: 0;
            padding: 0;
            width: 100%;
        }
        h1, h2, h3, h4, h5, h6 {
            font-family: 'Google Sans', 'Roboto', 'Arial', sans-serif;
            page-break-after: avoid;
            max-width: 100%;
        }
        h1 {
            color: #1a73e8;
            font-size: 26px;
            border-bottom: 1px solid #e0e0e0;
            padding-bottom: 8px;
            margin-top: 24px;
        }
        h2 {
            color: #188038;
            font-size: 20px;
            margin-top: 20px;
        }
        h3 {
            color: #f9ab00;
            font-size: 18px;
            margin-top: 18px;
        }
        h4 {
            color: #d93025;
            font-size: 16px;
            margin-top: 16px;
        }
        p, li {
            font-family: 'Google Sans', 'Roboto', 'Arial', sans-serif;
            word-wrap: break-word;
            overflow-wrap: break-word;
            max-width: 100%;
        }
        code {
            background-color: #f8f9fa;
            padding: 2px 6px;
            border-radius: 4px;
            font-family: 'Roboto Mono', 'Courier New', monospace;
            font-size: 90%;
            color: #d93025;
            word-break: break-word;
        }
        pre {
            background-color: #f8f9fa;
            padding: 12px;
            border: 1px solid #dadce0;
            border-radius: 8px;
            margin-bottom: 16px;
            white-space: pre-wrap;
            word-wrap: break-word;
            overflow-wrap: break-word;
            word-break: break-all;
            page-break-inside: avoid;
            width: 100%;
            max-width: 100%;
        }
        pre code {
            color: #3c4043;
            background-color: transparent;
            padding: 0;
            word-break: break-all;
        }
        table {
            width: 100%;
            max-width: 100%;
            border-collapse: collapse;
            margin-bottom: 20px;
            box-shadow: 0 1px 2px 0 rgba(60,64,67,0.3), 0 1px 3px 1px rgba(60,64,67,0.15);
            border-radius: 8px;
            overflow: hidden;
            table-layout: fixed;
        }
        th, td {
            border: 1px solid #e0e0e0;
            padding: 10px 12px;
            text-align: left;
            word-wrap: break-word;
            overflow-wrap: break-word;
            word-break: break-word;
            max-width: 100%;
            font-family: 'Google Sans', 'Roboto', 'Arial', sans-serif;
            font-size: 14px;
        }
        th {
            background-color: #f1f3f4;
            color: #202124;
            font-weight: 700;
        }
        tr:nth-child(even) {
            background-color: #f8f9fa;
        }
        tr:hover {
            background-color: #e8f0fe;
        }
        img {
            max-width: 100%;
            width: auto;
            height: auto;
            display: block;
            margin: 16px auto;
            border: 1px solid #dadce0;
            border-radius: 8px;
            padding: 8px;
            background-color: white;
            page-break-inside: avoid;
            box-sizing: border-box;
        }
        blockquote {
            border-left: 4px solid #1a73e8;
            background-color: #e8f0fe;
            padding: 10px 16px;
            margin: 16px 0;
            border-radius: 0 4px 4px 0;
            page-break-inside: avoid;
            max-width: 100%;
            word-wrap: break-word;
        }
        """
        
        pdf.add_section(Section(processed_report, paper_size=(400, 600)), user_css=google_css)
        
        # 3. Save to bytes
        pdf_buffer = io.BytesIO()
        pdf.save_bytes(pdf_buffer)
        pdf_bytes = pdf_buffer.getvalue()
        
        if not pdf_bytes:
            logging.error("Failed to generate PDF: bytes are empty")
            return False
            
        # 4. Save as artifact
        artifact_name = "Application_Modernization_Assessment_Report.pdf"
        artifact_part = Part(
            inline_data=Blob(
                data=pdf_bytes,
                mime_type="application/pdf",
                display_name=artifact_name
            )
        )
        
        await tool_context.save_artifact(
            filename=artifact_name,
            artifact=artifact_part
        )
        
        logging.info("PDF report saved as artifact: %s", artifact_name)
        return True
        
    except Exception as e:
        logging.exception("Error during PDF conversion: %s", e)
        return False
