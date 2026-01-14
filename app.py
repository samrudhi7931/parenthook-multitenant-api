from flask import Flask, request, jsonify, g
from flasgger import Swagger
from models import db, User, Organization
from middleware import tenant_middleware

app = Flask(__name__)

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///data.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db.init_app(app)
from flasgger import Swagger

swagger_config = {
    "swagger": "2.0",
    "headers": [],
    "uiversion": 3,
    "specs": [
        {
            "endpoint": "apispec_1",
            "route": "/apispec_1.json",
            "rule_filter": lambda rule: True,
            "model_filter": lambda tag: True,
        }
    ],
    "specs_route": "/apidocs/"  
}

Swagger(app, config=swagger_config)



@app.before_request
def before_request():
    # Allow home page
    if request.endpoint == "index":
        return

    # Allow Swagger UI and Swagger spec
    if request.path.startswith("/apidocs") or request.path.startswith("/apispec"):
        return

    # Apply tenant security to business APIs only
    return tenant_middleware()




@app.route("/")
def index():
    return "Multi-Tenant Flask App Running"

with app.app_context():
    db.create_all()

# -------- APIs --------

@app.route("/api/v1/users", methods=["POST"])
def create_user():
    """
    Create a new user
    ---
    tags:
      - Users
    parameters:
      - name: X-ORG-ID
        in: header
        type: integer
        required: true
      - in: body
        name: body
        required: true
        schema:
          type: object
          properties:
            name:
              type: string
            email:
              type: string
    responses:
      201:
        description: User created
    """

    data = request.json
    user = User(
        name=data["name"],
        email=data["email"],
        org_id=g.org_id
    )
    db.session.add(user)
    db.session.commit()
    return jsonify({"message": "User created"}), 201

@app.route("/api/v1/users", methods=["GET"])
def get_users():
    """
    Get users list (Multi-Tenant)
    ---
    tags:
      - Users
    parameters:
      - name: X-ORG-ID
        in: header
        type: integer
        required: true
        description: Organization ID
      - name: page
        in: query
        type: integer
        required: false
        description: Page number
      - name: search
        in: query
        type: string
        required: false
        description: Search by name
    responses:
      200:
        description: List of users
    """

    page = int(request.args.get("page", 1))
    search = request.args.get("search", "")

    query = User.query.filter(
        User.org_id == g.org_id,
        User.name.ilike(f"%{search}%")
    )

    users = query.paginate(page=page, per_page=5)

    return jsonify({
        "total": users.total,
        "page": page,
        "data": [{"id": u.id, "name": u.name, "email": u.email} for u in users.items]
    })

@app.errorhandler(Exception)
def handle_error(e):
    return jsonify({
        "error": "Internal Server Error",
        "message": str(e)
    }), 500

if __name__ == "__main__":
    app.run(debug=True)
