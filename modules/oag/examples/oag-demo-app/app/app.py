#!/usr/bin/env python3
"""
OAG Demo Application

A simple Flask application that displays HTTP headers injected by
Okta Access Gateway. Useful for testing and demonstrating header-based
authentication.

Usage:
    python app.py
    # Or with Docker
    docker build -t oag-demo-app .
    docker run -p 8080:8080 oag-demo-app
"""

import os
from flask import Flask, request, render_template_string, jsonify

app = Flask(__name__)

# HTML template for displaying headers
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>OAG Demo App - Header Viewer</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
            max-width: 900px;
            margin: 0 auto;
            padding: 20px;
            background: #f5f5f5;
        }
        .container {
            background: white;
            border-radius: 8px;
            padding: 20px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            margin-bottom: 20px;
        }
        h1 {
            color: #1a73e8;
            margin-top: 0;
        }
        h2 {
            color: #333;
            border-bottom: 2px solid #1a73e8;
            padding-bottom: 10px;
        }
        .user-info {
            background: #e8f0fe;
            padding: 15px;
            border-radius: 4px;
            margin-bottom: 20px;
        }
        .user-info h3 {
            margin-top: 0;
            color: #1a73e8;
        }
        .user-info p {
            margin: 5px 0;
        }
        .header-table {
            width: 100%;
            border-collapse: collapse;
        }
        .header-table th, .header-table td {
            text-align: left;
            padding: 10px;
            border-bottom: 1px solid #ddd;
        }
        .header-table th {
            background: #f8f9fa;
            font-weight: 600;
        }
        .header-name {
            font-family: monospace;
            color: #d93025;
        }
        .header-value {
            font-family: monospace;
            word-break: break-all;
        }
        .oag-header {
            background: #e6f4ea;
        }
        .status {
            display: inline-block;
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 12px;
            font-weight: 600;
        }
        .status-authenticated {
            background: #34a853;
            color: white;
        }
        .status-unauthenticated {
            background: #ea4335;
            color: white;
        }
        footer {
            text-align: center;
            color: #666;
            font-size: 12px;
            margin-top: 20px;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🔐 OAG Demo Application</h1>
        <p>This application displays HTTP headers injected by Okta Access Gateway.</p>

        <div class="user-info">
            <h3>Authenticated User</h3>
            {% if user %}
                <span class="status status-authenticated">AUTHENTICATED</span>
                <p><strong>Username:</strong> {{ user.username or 'N/A' }}</p>
                <p><strong>Email:</strong> {{ user.email or 'N/A' }}</p>
                <p><strong>Name:</strong> {{ user.first_name or '' }} {{ user.last_name or '' }}</p>
            {% else %}
                <span class="status status-unauthenticated">NOT AUTHENTICATED</span>
                <p>No OAG authentication headers detected.</p>
            {% endif %}
        </div>
    </div>

    <div class="container">
        <h2>OAG Injected Headers</h2>
        {% if oag_headers %}
        <table class="header-table">
            <thead>
                <tr>
                    <th>Header Name</th>
                    <th>Value</th>
                </tr>
            </thead>
            <tbody>
                {% for name, value in oag_headers %}
                <tr class="oag-header">
                    <td class="header-name">{{ name }}</td>
                    <td class="header-value">{{ value }}</td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
        {% else %}
        <p>No OAG headers detected. Common OAG headers include:</p>
        <ul>
            <li><code>X-Remote-User</code></li>
            <li><code>X-Remote-Email</code></li>
            <li><code>REMOTE_USER</code></li>
        </ul>
        {% endif %}
    </div>

    <div class="container">
        <h2>All Request Headers</h2>
        <table class="header-table">
            <thead>
                <tr>
                    <th>Header Name</th>
                    <th>Value</th>
                </tr>
            </thead>
            <tbody>
                {% for name, value in all_headers %}
                <tr>
                    <td class="header-name">{{ name }}</td>
                    <td class="header-value">{{ value }}</td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
    </div>

    <footer>
        OAG Demo App v1.0 | Part of <a href="https://github.com/joevanhorn/okta-terraform-demo-template">Okta Terraform Demo Template</a>
    </footer>
</body>
</html>
"""

# Common OAG header patterns
OAG_HEADER_PATTERNS = [
    'X-Remote-',
    'X-Forwarded-',
    'X-User-',
    'REMOTE_USER',
    'X-OAG-',
    'X-Okta-',
]


def is_oag_header(header_name: str) -> bool:
    """Check if a header is likely injected by OAG."""
    header_upper = header_name.upper()
    return any(pattern.upper() in header_upper for pattern in OAG_HEADER_PATTERNS)


def get_user_from_headers(headers: dict) -> dict:
    """Extract user information from OAG headers."""
    user = {}

    # Try different header name patterns
    username_headers = ['X-Remote-User', 'REMOTE_USER', 'X-User-Id', 'X-Forwarded-User']
    email_headers = ['X-Remote-Email', 'X-User-Email', 'X-Forwarded-Email']
    firstname_headers = ['X-Remote-FirstName', 'X-User-FirstName', 'X-Remote-First-Name']
    lastname_headers = ['X-Remote-LastName', 'X-User-LastName', 'X-Remote-Last-Name']

    for header in username_headers:
        if header in headers:
            user['username'] = headers[header]
            break

    for header in email_headers:
        if header in headers:
            user['email'] = headers[header]
            break

    for header in firstname_headers:
        if header in headers:
            user['first_name'] = headers[header]
            break

    for header in lastname_headers:
        if header in headers:
            user['last_name'] = headers[header]
            break

    return user if user else None


@app.route('/')
def index():
    """Main page displaying all headers."""
    # Get all headers
    headers = dict(request.headers)

    # Separate OAG headers
    oag_headers = [(k, v) for k, v in sorted(headers.items()) if is_oag_header(k)]
    all_headers = sorted(headers.items())

    # Extract user info
    user = get_user_from_headers(headers)

    return render_template_string(
        HTML_TEMPLATE,
        user=user,
        oag_headers=oag_headers,
        all_headers=all_headers
    )


@app.route('/health')
def health():
    """Health check endpoint for load balancer."""
    return jsonify({
        'status': 'healthy',
        'service': 'oag-demo-app'
    })


@app.route('/api/headers')
def api_headers():
    """API endpoint returning headers as JSON."""
    headers = dict(request.headers)
    user = get_user_from_headers(headers)

    return jsonify({
        'user': user,
        'oag_headers': {k: v for k, v in headers.items() if is_oag_header(k)},
        'all_headers': headers
    })


@app.route('/api/user')
def api_user():
    """API endpoint returning authenticated user info."""
    headers = dict(request.headers)
    user = get_user_from_headers(headers)

    if user:
        return jsonify({
            'authenticated': True,
            'user': user
        })
    else:
        return jsonify({
            'authenticated': False,
            'user': None
        }), 401


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    debug = os.environ.get('DEBUG', 'false').lower() == 'true'

    print(f"Starting OAG Demo App on port {port}")
    app.run(host='0.0.0.0', port=port, debug=debug)
