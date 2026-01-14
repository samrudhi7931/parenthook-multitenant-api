from flask import request, jsonify, g

def tenant_middleware():
    org_id = request.headers.get("X-ORG-ID")
    if not org_id:
        return jsonify({"error": "X-ORG-ID header is required"}), 400
    g.org_id = int(org_id)
