from flask import Blueprint, request, jsonify
from db import get_db_connection
import json

feedback_bp = Blueprint('feedback', __name__)

@feedback_bp.route('/api/feedback/submit', methods=['POST'])
def submit_feedback():
    data = request.get_json()
    session_id = data.get('session_id')
    message = data.get('message')

    if not session_id or not message:
        return jsonify({"error": "Missing data"}), 400

    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO feedback (session_id, message)
            VALUES (%s, %s)
        """, (session_id, message))
        conn.commit()
        return jsonify({"message": "Feedback saved ✅"}), 200

    except Exception as e:
        print("⚠️ FEEDBACK HATASI:", e)  # 👈 Bunu EKLE!
        return jsonify({"error": str(e)}), 500

    finally:
        cursor.close()
        conn.close()


@feedback_bp.route('/api/feedback/by_teacher', methods=['POST'])
def get_feedback_by_teacher():
    data = request.get_json()
    teacher_id = data.get('teacher_id')

    if not teacher_id:
        return jsonify({"error": "Missing teacher_id"}), 400

    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT f.message, f.submitted_at, s.title 
            FROM feedback f
            JOIN sessions s ON f.session_id = s.id
            WHERE s.teacher_id = %s
            ORDER BY f.submitted_at DESC
        """, (teacher_id,))
        feedbacks = cursor.fetchall()
        return jsonify(feedbacks), 200
    except Exception as e:
        print("⚠️ FEEDBACK ÇEKME HATASI:", e)
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()
