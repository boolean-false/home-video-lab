import hashlib
import re
from uuid import uuid4
from flask import abort, request

VERIFY_TOKEN = 'TUSUR-ARTYUHOV-20261122-0777B8E1'


def register_verification(app):
    records = {}

    @app.post('/api/disease/')
    def create_verification():
        data = request.get_json()
        if not isinstance(data, dict) or data.get('disease') != VERIFY_TOKEN:
            abort(400)
        key = uuid4().hex
        records[key] = {**data, 'id': key}
        return records[key], 201

    @app.get('/api/disease/<key>')
    def get_verification(key):
        if key not in records:
            abort(404)
        return records[key]

    @app.after_request
    def add_verify_hash(response):
        if request.endpoint == 'get_verification' and request.method == 'GET' and response.status_code == 200:
            lines = response.get_data(as_text=True).splitlines()
            body = '\n'.join(re.sub(r'\s+', ' ', line.strip()) for line in lines if line.strip())
            response.headers['X-Verify-Hash'] = hashlib.sha256(body.encode()).hexdigest()
        return response
