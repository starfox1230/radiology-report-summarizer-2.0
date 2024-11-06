from openai import OpenAI
from flask import Flask, render_template, request
import os

app = Flask(__name__)

# Initialize the OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Function to send text to GPT-4o-mini and get a summary
def get_summary(case_text, custom_prompt):
    try:
        # Use the client object and chat completion call
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a helpful assistant that organizes changes made by attendings to residents' radiology reports."},
                {"role": "user", "content": f"{custom_prompt}\n{case_text}"}
            ],
            max_tokens=2000,
            temperature=0.5
        )
        # Correct way to access the message content
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"Error processing case: {str(e)}"

# Function to process multiple cases from bulk input
def process_cases(bulk_text, custom_prompt):
    summaries = []
    # Split the input into individual cases by the word "Case"
    cases = bulk_text.split("Case")
    for index, case in enumerate(cases[1:], start=1):  # Skipping the empty string from the split
        if "Attending Report" in case and "Resident Report" in case:
            attending_report = case.split("Attending Report:")[1].split("Resident Report:")[0].strip()
            resident_report = case.split("Resident Report:")[1].strip()
            case_text = f"Resident Report: {resident_report}\nAttending Report: {attending_report}"
            summary = get_summary(case_text, custom_prompt)
            summaries.append(f"Case {index}:\n{summary}\n")
    return summaries

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/process', methods=['POST'])
def process():
    bulk_text = request.form['case_text']
    custom_prompt = request.form['custom_prompt']
    summaries = process_cases(bulk_text, custom_prompt)
    summary_output = "\n".join(summaries)
    return render_template('index.html', case_text=bulk_text, summary=summary_output)

if __name__ == "__main__":
    app.run(debug=True)
