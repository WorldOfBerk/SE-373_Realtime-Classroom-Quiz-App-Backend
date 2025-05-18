from flask import Blueprint, request, jsonify
from db import get_db_connection
import random
import string

session_bp = Blueprint('session', __name__)

def generate_session_code(length=5):
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))

@session_bp.route('/api/session/create', methods=['POST'])
def create_session():
    data = request.get_json()
    title = data.get('title')
    teacher_id = data.get('teacher_id')

    if not title or not teacher_id:
        return jsonify({"error": "title and teacher_id are required"}), 400

    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        # Benzersiz kod üret
        code = generate_session_code()
        cursor.execute("SELECT * FROM sessions WHERE code = %s", (code,))
        while cursor.fetchone():
            code = generate_session_code()

        # Session'ı oluştur
        cursor.execute("""
            INSERT INTO sessions (code, title, created_by) 
            VALUES (%s, %s, %s)
        """, (code, title, teacher_id))
        conn.commit()

        return jsonify({"message": "Session created", "code": code, "session_id": cursor.lastrowid}), 200


    except Exception as e:
        return jsonify({"error": str(e)}), 500

    finally:
        cursor.close()
        conn.close()


@session_bp.route('/api/session/join', methods=['POST'])
def join_session():
    data = request.get_json()
    code = data.get('code')
    student_id = data.get('student_id')

    if not code or not student_id:
        return jsonify({"error": "code and student_id are required"}), 400

    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("SELECT id FROM sessions WHERE code = %s", (code,))
        session = cursor.fetchone()
        if not session:
            return jsonify({"error": "Invalid session code"}), 404

        session_id = session['id']

        cursor.execute("SELECT * FROM session_participants WHERE session_id = %s AND student_id = %s", (session_id, student_id))
        if cursor.fetchone():
            return jsonify({"message": "Already joined", "session_id": session_id}), 200

        cursor.execute("INSERT INTO session_participants (session_id, student_id) VALUES (%s, %s)", (session_id, student_id))
        conn.commit()

        return jsonify({"message": "Joined successfully", "session_id": session_id}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

    finally:
        cursor.close()
        conn.close()
