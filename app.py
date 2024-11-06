from openai import OpenAI
from flask import Flask, render_template, request
import os
import json

app = Flask(__name__)

# Initialize the OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Function to send text to OpenAI and get a structured JSON summary
def get_summary(case_text, custom_prompt, case_number):
    try:
        # Use the client object to request structured JSON output
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a helpful assistant that outputs structured JSON summaries of radiology report differences."},
                {"role": "user", "content": f"{custom_prompt}\nCase Number: {case_number}\n{case_text}"}
            ],
            max_tokens=2000,
            temperature=0.5
        )

        # Capture and check the API response
        json_output = response.choices[0].message.content.strip()
        
        # Verify if the response is valid JSON
        try:
            parsed_json = json.loads(json_output)
            return parsed_json
        except json.JSONDecodeError:
            # Log an error if JSON decoding fails
            print(f"Failed to decode JSON for case {case_number}: {json_output}")
            return {"error": f"Invalid JSON response from API for case {case_number}"}
    
    except Exception as e:
        # Log other exceptions and return an error message
        print(f"Error processing case {case_number}: {str(e)}")
        return {"error": f"Error processing case {case_number}: {str(e)}"}

# Function to process multiple cases and structure the output as JSON with scores
def process_cases(bulk_text, custom_prompt):
    cases = bulk_text.split("Case")  # Split input text into individual cases
    structured_output = []  # List to hold JSON outputs for each case

    for index, case in enumerate(cases[1:], start=1):  # Skip the empty first element
        if "Attending Report" in case and "Resident Report" in case:
            # Extract attending and resident reports from each case
            attending_report = case.split("Attending Report:")[1].split("Resident Report:")[0].strip()
            resident_report = case.split("Resident Report:")[1].strip()
            case_text = f"Resident Report: {resident_report}\nAttending Report: {attending_report}"
            
            # Get structured JSON summary for each case
            parsed_json = get_summary(case_text, custom_prompt, case_number=index)
            
            # Check if there's an error in the parsed JSON
            if "error" in parsed_json:
                structured_output.append({"case_number": index, "error": parsed_json["error"]})
            else:
                # Calculate the score if there is no error
                score = len(parsed_json.get('major_findings', [])) * 3 + len(parsed_json.get('minor_findings', [])) * 1
                parsed_json['score'] = score  # Append score to the JSON
                structured_output.append(parsed_json)

    # Return the structured output as a list (not a JSON string)
    return structured_output

@app.route('/')
def index():
    return render_template('index.html', case_text="", summary=[])

@app.route('/process', methods=['POST'])
def process():
    bulk_text = request.form['case_text']
    custom_prompt = request.form['custom_prompt']
    structured_summary = process_cases(bulk_text, custom_prompt)  # Get structured JSON output
    return render_template('index.html', case_text=bulk_text, summary=structured_summary)

if __name__ == "__main__":
    app.run(debug=True)
