import logging
import io
import re
import base64
import requests
import os
import json
from google.adk.tools import ToolContext
from google.genai.types import Part, Blob
from jinja2 import Environment, FileSystemLoader
from weasyprint import HTML, CSS
from markdown_it import MarkdownIt

def generate_pdf_from_dynamic_schema(json_payload: dict, template_dir: str) -> bytes:
    """
    Polymorphically parses structured blocks, downloads raw diagram dependencies 
    into temporary image assets, renders Jinja HTML, and compiles via WeasyPrint.
    """
    processed_blocks = []
    temp_files_to_cleanup = []
    md = MarkdownIt()
    
    for i, block in enumerate(json_payload.get("content_blocks", [])):
        b_type = block.get("block_type")
        
        if b_type == "architectural_diagram":
            code = block.get("source_code", "").strip()
            encoded = base64.b64encode(code.encode('utf-8')).decode('utf-8')
            url = f"https://mermaid.ink/img/{encoded}"
            
            img_path = f"/tmp/mermaid_diagram_{i}.png"
            try:
                r = requests.get(url, timeout=10)
                if r.status_code == 200:
                    with open(img_path, "wb") as f:
                        f.write(r.content)
                    block["preprocessed_image_path"] = img_path
                    temp_files_to_cleanup.append(img_path)
                else:
                    block["block_type"] = "code_diff"
                    block["filename"] = "Failed Diagram Render (Raw Code)"
                    block["diff_string"] = code
            except Exception:
                block["block_type"] = "code_diff"
                block["filename"] = "Failed Diagram Render (Raw Code)"
                block["diff_string"] = code
                
        elif b_type in ["paragraph", "callout_box"]:
            for key in ["text", "content"]:
                if block.get(key):
                    block[key] = md.render(str(block[key]))
                    
        elif b_type in ["bullet_list", "numbered_list"]:
            items = block.get("items", [])
            rendered_items = []
            for item in items:
                rendered_items.append(md.renderInline(str(item)))
            block["items"] = rendered_items
            
                    
        elif b_type == "code_diff":
            raw_diff = block.get("diff_string", "")
            diff_lines_html = []
            for line in raw_diff.splitlines():
                clean_line = line.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
                if clean_line.startswith('+'):
                    diff_lines_html.append(f'<div class="diff-line plus">{clean_line}</div>')
                elif clean_line.startswith('-'):
                    diff_lines_html.append(f'<div class="diff-line minus">{clean_line}</div>')
                elif clean_line.startswith('@@'):
                    diff_lines_html.append(f'<div class="diff-line header">{clean_line}</div>')
                else:
                    diff_lines_html.append(f'<div class="diff-line regular">{clean_line}</div>')
            block["diff_html"] = "\n".join(diff_lines_html)
            
                    
        processed_blocks.append(block)
        
    json_payload["content_blocks"] = processed_blocks
    
    env = Environment(loader=FileSystemLoader(template_dir))
    template = env.get_template("executive_report_template.html")
    rendered_html = template.render(**json_payload)
    
    weasy_html = HTML(string=rendered_html, base_url=template_dir)
    pdf_bytes = weasy_html.write_pdf(stylesheets=[CSS(os.path.join(template_dir, "google_material.css"))])
    
    for tmp in temp_files_to_cleanup:
        if os.path.exists(tmp):
            os.remove(tmp)
            
    return pdf_bytes

async def convert_report_to_pdf(report_content: str, tool_context: ToolContext) -> bool:
    """
    Converts a structured assessment report into a publication-grade PDF artifact.
    """
    logging.info("Converting structured report findings to PDF...")
    
    try:
        report_json = None
        clean_text = report_content.strip()
        if clean_text.startswith("```json"):
            clean_text = clean_text[7:]
            if clean_text.endswith("```"):
                clean_text = clean_text[:-3]
            clean_text = clean_text.strip()
        
        try:
            report_json = json.loads(clean_text)
        except Exception as json_err:
            logging.info("Input content is not strict JSON (%s). Applying raw fallback schema wrapper...", json_err)
            report_json = {
                "report_title": "Application Modernization Assessment Report (Fallback Layout)",
                "metadata_summary": {
                    "evaluation_note": "Unformatted raw text recovery mode"
                },
                "content_blocks": [
                    {
                        "block_type": "paragraph",
                        "text": report_content
                    }
                ]
            }

        template_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../app/templates"))
        if not os.path.exists(template_dir):
            template_dir = "/code/app/templates"
            
        pdf_bytes = generate_pdf_from_dynamic_schema(report_json, template_dir)
        
        if not pdf_bytes:
            logging.error("Failed to generate PDF: bytes are empty")
            return False
            
        # Save as artifact
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
