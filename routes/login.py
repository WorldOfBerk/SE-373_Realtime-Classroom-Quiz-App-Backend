from flask import Blueprint, request, jsonify
from db import get_db_connection
import bcrypt

login_bp = Blueprint('login', __name__)

@login_bp.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    user_id = data.get('id')
    password = data.get('password')

    if not user_id or not password:
        return jsonify({"error": "ID and password are required"}), 400

    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
        user = cursor.fetchone()
        if not user:
            return jsonify({"error": "User not found"}), 404

        if not bcrypt.checkpw(password.encode('utf-8'), user['password'].encode('utf-8')):
            return jsonify({"error": "Incorrect password"}), 401

        role = user['role']
        extra_info = {}

        if role == 'student':
            cursor.execute("""
                SELECT name, surname, department, faculty 
                FROM students WHERE id = %s
            """, (user_id,))
            info = cursor.fetchone()
            if info: extra_info.update(info)

        elif role == 'teacher':
            cursor.execute("""
                SELECT name, surname, department, faculty 
                FROM teachers WHERE id = %s
            """, (user_id,))
            info = cursor.fetchone()
            if info: extra_info.update(info)

        return jsonify({
            "message": "Login successful",
            "id": user['id'],
            "role": role,
            **extra_info
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500

    finally:
        cursor.close()
        conn.close()


