from flask import Flask, render_template, request, Markup
import os
import shutil
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()

GEN_API_KEY = os.getenv("GEN_API_KEY")
genai.configure(api_key=GEN_API_KEY)

generation_config = {
    "temperature": 1,
    "top_p": 0.95,
    "top_k": 64,
    "max_output_tokens": 8192,
}

model = genai.GenerativeModel(
    model_name="gemini-1.5-pro-latest",
    generation_config=generation_config,
)


app = Flask(__name__)

UPLOAD_FOLDER = 'uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def upload_to_gemini(path, mime_type=None):
    return genai.upload_file(path, mime_type=mime_type)

def parse_markdown_table(markdown_text):
    
    lines = markdown_text.strip().split('\n')

    
    table_start = next((i for i, line in enumerate(lines) if line.startswith('|')), None)
    if table_start is None:
        return None

    table_end = next((i for i, line in enumerate(lines[table_start:]) if not line.strip().startswith('|')), len(lines))
    table_lines = lines[table_start:table_start + table_end]

    
    headers = [cell.strip() for cell in table_lines[0].split('|')[1:-1]]
    rows = []
    for line in table_lines[2:]:  
        cells = [cell.strip() for cell in line.split('|')[1:-1]]
        rows.append(cells)

    return headers, rows

def markdown_to_html_table(markdown_text):
    parsed_table = parse_markdown_table(markdown_text)
    if parsed_table is None:
        return "<p>No table found in the response.</p>"

    headers, rows = parsed_table

    html = "<table border='1'><thead><tr>"
    for header in headers:
        html += f"<th>{header}</th>"
    html += "</tr></thead><tbody>"

    for row in rows:
        html += "<tr>"
        for cell in row:
            html += f"<td>{cell}</td>"
        html += "</tr>"

    html += "</tbody></table>"
    return html

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        text_input = request.form.get('text_input', '')
        uploaded_files = request.files.getlist('images')

        if not uploaded_files:
            return "Error: No files uploaded", 400

        gemini_files = []
        for file in uploaded_files:
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
            file.save(file_path)
            gemini_file = upload_to_gemini(file_path, mime_type=file.mimetype)
            gemini_files.append(gemini_file)

        prompt = f'''Generate test cases for the app in the screenshots. If there are multiple screenshots, consider them all to be related to a single app and generate test cases accordingly.
        For the text enclosed by backticks, if anything is present, take it into consideration too:
        `{text_input}`
        Please format your response as a markdown table with the following columns:
        Test Case ID | Test Case Description | Pre-Conditions | Test Steps | Expected Results'''

        try:
            response = model.generate_content([*gemini_files, prompt])
            table_html = markdown_to_html_table(response.text)
            return Markup(f"<h2>Generated Test Cases:</h2>{table_html}")
        except Exception as e:
            return f"An error occurred: {str(e)}", 500

    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)
    
shutil.rmtree('uploads')
