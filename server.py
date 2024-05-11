from flask import Flask, request, jsonify, render_template_string
import json
import redis
import uuid
from datetime import datetime

app = Flask(__name__)
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0  # Prevent caching

# Create Redis connection
r = redis.Redis()

@app.route('/')
def index():
    return render_template_string('''
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Submit Image URL</title>
        <link href="https://stackpath.bootstrapcdn.com/bootstrap/4.5.2/css/bootstrap.min.css" rel="stylesheet">
    </head>
    <body>
        <div class="container mt-5">
            <h2 class="mb-3">Submit Image URL for Processing</h2>
            <form action="/process" method="post" class="mb-3">
                <div class="form-group">
                    <label for="url">Image URL:</label>
                    <input type="text" class="form-control" id="url" name="url" placeholder="Enter Image URL here" required>
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
    if 'url' in request.form:
        url = request.form['url']
        message = {
            "task_id": task_id,
            "timestamp": str(datetime.now()),
            "url": url
        }
        r.lpush("download", json.dumps(message))
    return render_template_string('''
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <title>Image Processing Results</title>
        <link href="https://stackpath.bootstrapcdn.com/bootstrap/4.5.2/css/bootstrap.min.css" rel="stylesheet">
        <script>
            function checkResult() {
                document.getElementById('loading').style.display = 'block';  // Show loading text
                fetch('/api/result/{{ task_id }}').then(function(response) {
                    return response.json();
                }).then(function(data) {
                    document.getElementById('loading').style.display = 'none';  // Hide loading text
                    if ('error' in data) {
                        setTimeout(checkResult, 2000);
                    } else {
                        document.getElementById('result').textContent = JSON.stringify(data, null, 2);
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
            <pre id="result"></pre>
        </div>
    </body>
    </html>
    ''', task_id=task_id)

@app.route('/api/result/<task_id>', methods=['GET'])
def api_get_result(task_id):
    result = r.get(f"result:{task_id}")
    if result:
        return jsonify(json.loads(result.decode('utf-8'))), 200
    else:
        return jsonify({"error": "Result not found. Please wait."}), 202

if __name__ == "__main__":
    app.run(host='localhost', port=5000)
