from flask import Flask, request, jsonify, render_template_string
import json
import redis
import uuid
from datetime import datetime

app = Flask(__name__)
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0  # Prevent caching

# Create Redis connection
r = redis.Redis()

# Dictionary mapping short forms to full language names
language_map = {
    'ar': 'Arabic',
    'bg': 'Bulgarian',
    'de': 'German',
    'el': 'Modern Greek',
    'en': 'English',
    'es': 'Spanish',
    'fr': 'French',
    'hi': 'Hindi',
    'it': 'Italian',
    'ja': 'Japanese',
    'nl': 'Dutch',
    'pl': 'Polish',
    'pt': 'Portuguese',
    'ru': 'Russian',
    'sw': 'Swahili',
    'th': 'Thai',
    'tr': 'Turkish',
    'ur': 'Urdu',
    'vi': 'Vietnamese',
    'zh': 'Chinese'
}

@app.route('/')
def index():
    return render_template_string('''
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Submit Text</title>
        <link href="https://stackpath.bootstrapcdn.com/bootstrap/4.5.2/css/bootstrap.min.css" rel="stylesheet">
    </head>
    <body>
        <div class="container mt-5">
            <h2 class="mb-3">Submit Text for Language Detection</h2>
            <form action="/process" method="post" class="mb-3">
                <div class="form-group">
                    <label for="text">Text:</label>
                    <textarea class="form-control" id="text" name="text" rows="5" placeholder="Enter text here" required></textarea>
                </div>
                <button type="submit" class="btn btn-primary">Submit</button>
            </form>
        </div>
    </body>
    </html>
    ''')

@app.route('/process', methods=['POST'])
def process_request():
    task_id = str(uuid.uuid4())
    if 'text' in request.form:
        text = request.form['text']
        message = {
            "task_id": task_id,
            "timestamp": str(datetime.now()),
            "text": text
        }
        r.lpush("text", json.dumps(message))
    return render_template_string('''
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <title>Language Detection Results</title>
        <link href="https://stackpath.bootstrapcdn.com/bootstrap/4.5.2/css/bootstrap.min.css" rel="stylesheet">
        <script>
            const languageMap = {{ language_map|tojson }};
            function checkResult() {
                document.getElementById('loading').style.display = 'block';  // Show loading text
                fetch('/api/result/{{ task_id }}').then(function(response) {
                    return response.json();
                }).then(function(data) {
                    document.getElementById('loading').style.display = 'none';  // Hide loading text
                    if ('error' in data) {
                        setTimeout(checkResult, 2000);
                    } else {
                        let tableHtml = '<table class="table">';
                        tableHtml += '<thead><tr><th>Language Code</th><th>Language</th><th>Score</th></tr></thead>';
                        tableHtml += '<tbody>';
                        data.predictions.forEach(function(prediction) {
                            let languageCode = prediction.label;
                            let languageName = languageMap[languageCode] || 'Unknown';
                            tableHtml += '<tr>';
                            tableHtml += '<td>' + languageCode + '</td>';
                            tableHtml += '<td>' + languageName + '</td>';
                            tableHtml += '<td>' + prediction.score.toFixed(4) + '</td>';
                            tableHtml += '</tr>';
                        });
                        tableHtml += '</tbody></table>';
                        document.getElementById('result').innerHTML = tableHtml;
                    }
                });
            }
            window.onload = checkResult;
        </script>
    </head>
    <body>
        <div class="container mt-5">
            <h1>Results for Task ID: {{ task_id }}</h1>
            <p id="loading" style="display:none;">Loading results...</p>
            <div id="result"></div>
        </div>
    </body>
    </html>
    ''', task_id=task_id, language_map=language_map)

@app.route('/api/result/<task_id>', methods=['GET'])
def api_get_result(task_id):
    result = r.get(f"result:{task_id}")
    if result:
        return jsonify(json.loads(result.decode('utf-8'))), 200
    else:
        return jsonify({"error": "Result not found. Please wait."}), 202

if __name__ == "__main__":
    app.run(host='localhost', port=5000)