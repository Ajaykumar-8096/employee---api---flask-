from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from db import get_db_connection
import re

employee_bp = Blueprint("employee", __name__)

def valid_email(email):
    return re.match(r"[^@]+@[^@]+\.[^@]+", email)


@employee_bp.route("/employees/", methods=["POST"])
@jwt_required()
def create_employee():
    data = request.json

    if not data.get("name") or not valid_email(data.get("email")):
        return jsonify(message="Invalid input"), 400

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT id FROM employees WHERE email=%s", (data["email"],))
    if cursor.fetchone():
        return jsonify(message="Email already exists"), 400

    cursor.execute(
        "INSERT INTO employees (name, email, department, role) VALUES (%s,%s,%s,%s)",
        (data["name"], data["email"], data.get("department"), data.get("role"))
    )
    conn.commit()
    conn.close()

    return jsonify(message="Employee created"), 201


@employee_bp.route("/employees/", methods=["GET"])
@jwt_required()
def list_employees():
    page = int(request.args.get("page", 1))
    department = request.args.get("department")
    role = request.args.get("role")

    limit = 10
    offset = (page - 1) * limit

    query = "SELECT * FROM employees WHERE 1=1"
    params = []

    if department:
        query += " AND department=%s"
        params.append(department)
    if role:
        query += " AND role=%s"
        params.append(role)

    query += " LIMIT %s OFFSET %s"
    params.extend([limit, offset])

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(query, params)
    employees = cursor.fetchall()
    conn.close()

    return jsonify(employees), 200


@employee_bp.route("/employees/<int:id>/", methods=["GET"])
@jwt_required()
def get_employee(id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM employees WHERE id=%s", (id,))
    emp = cursor.fetchone()
    conn.close()

    if not emp:
        return jsonify(message="Employee not found"), 404

    return jsonify(emp), 200


@employee_bp.route("/employees/<int:id>/", methods=["PUT"])
@jwt_required()
def update_employee(id):
    data = request.json

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT id FROM employees WHERE id=%s", (id,))
    if not cursor.fetchone():
        conn.close()
        return jsonify(message="Employee not found"), 404

    cursor.execute(
        "UPDATE employees SET name=%s, department=%s, role=%s WHERE id=%s",
        (data.get("name"), data.get("department"), data.get("role"), id)
    )
    conn.commit()
    conn.close()

    return jsonify(message="Employee updated"), 200


@employee_bp.route("/employees/<int:id>/", methods=["DELETE"])
@jwt_required()
def delete_employee(id):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT id FROM employees WHERE id=%s", (id,))
    if not cursor.fetchone():
        conn.close()
        return jsonify(message="Employee not found"), 404

    cursor.execute("DELETE FROM employees WHERE id=%s", (id,))
    conn.commit()
    conn.close()

    return "", 204
