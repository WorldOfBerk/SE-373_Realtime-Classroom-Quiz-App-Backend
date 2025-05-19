from flask import Blueprint, request, jsonify
from db import get_db_connection
import json

quiz_bp = Blueprint('quiz', __name__)

@quiz_bp.route('/api/quiz/create', methods=['POST'])
def create_quiz():
    data = request.get_json()
    session_id = data.get('session_id')
    question = data.get('question')
    quiz_type = data.get('type')  # 'quiz' or 'poll'
    options = data.get('options')  # array/list
    correct_option = data.get('correct_option')

    if not session_id or not question or not options or not quiz_type:
        return jsonify({"error": "Missing required fields"}), 400

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO quizzes (session_id, question, type, options, correct_option)
            VALUES (%s, %s, %s, %s, %s)
        """, (
            session_id, question, quiz_type,
            json.dumps(options), correct_option if quiz_type == "quiz" else None
        ))

        conn.commit()
        return jsonify({"message": "Quiz created"}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

    finally:
        cursor.close()
        conn.close()


@quiz_bp.route('/api/quiz/active', methods=['POST'])
def get_active_quiz():
    data = request.get_json()
    session_id = data.get('session_id')

    if not session_id:
        return jsonify({"error": "session_id is required"}), 400

    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("""
            SELECT id, question, type, options
            FROM quizzes
            WHERE session_id = %s AND is_active = TRUE
            ORDER BY created_at DESC
            LIMIT 1
        """, (session_id,))
        quiz = cursor.fetchone()

        if not quiz:
            return jsonify({"message": "No active quiz"}), 204

        import json
        quiz["options"] = json.loads(quiz["options"])

        return jsonify(quiz), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

    finally:
        cursor.close()
        conn.close()

@quiz_bp.route('/api/quiz/answer', methods=['POST'])
def submit_answer():
    try:
        data = request.get_json()
        print("GELEN VERİ:", data)

        quiz_id = data.get('quiz_id')
        student_id = data.get('student_id')
        selected_option = data.get('selected_option')

        if not quiz_id or not student_id or selected_option is None:
            return jsonify({"error": "Eksik alan var"}), 400

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT 1 FROM quiz_answers WHERE quiz_id = %s AND student_id = %s", (quiz_id, student_id))
        if cursor.fetchone():
            return jsonify({"message": "You already answered this quiz"}), 409

        cursor.execute("SELECT correct_option FROM quizzes WHERE id = %s", (quiz_id,))
        result = cursor.fetchone()
        if not result:
            return jsonify({"error": "Quiz bulunamadı"}), 404

        correct_option = result[0]
        is_correct = (selected_option == correct_option)

        cursor.execute("""
            INSERT INTO quiz_answers (quiz_id, student_id, selected_option, is_correct)
            VALUES (%s, %s, %s, %s)
        """, (quiz_id, student_id, selected_option, is_correct))

        if is_correct:
            cursor.execute("UPDATE students SET points = points + 5 WHERE id = %s", (student_id,))

        conn.commit()

        return jsonify({
            "message": "Cevap alındı",
            "is_correct": is_correct
        }), 200

    except Exception as e:
        print("⚠️ HATA:", e)
        return jsonify({"error": str(e)}), 500

    finally:
        try:
            cursor.close()
            conn.close()
        except:
            pass


@quiz_bp.route('/api/quiz/multi', methods=['POST'])
def create_multiple_quizzes():
    try:
        data = request.get_json()
        print("📦 Received JSON:", data)
        print("📦 Type:", type(data))

        if not isinstance(data, list):
            print("❌ not JSON list!")
            return jsonify({"error": "Payload must be a list"}), 400

        conn = get_db_connection()
        cursor = conn.cursor()

        for index, item in enumerate(data):
            print(f"🔍 İşleniyor -> {index + 1}. Soru:", item)

            session_id = item.get('session_id')
            teacher_id = item.get('teacher_id')
            question = item.get('question')
            options = item.get('options')
            correct_option = item.get('correct_option')

            print(f"➡️ session_id={session_id}, teacher_id={teacher_id}, question={question}, correct_option={correct_option}")
            print(f"➡️ options={options}, tipi={type(options)}")

            if not all([session_id, teacher_id, question, options, correct_option is not None]):
                print("Missing Field!")
                return jsonify({"error": "Missing fields in some quiz item"}), 400

            options_str = json.dumps(options)
            cursor.execute("""
                INSERT INTO quizzes (session_id, teacher_id, question, options, correct_option)
                VALUES (%s, %s, %s, %s, %s)
            """, (session_id, teacher_id, question, options_str, correct_option))

        conn.commit()
        print("✅ All questions added successfully")
        return jsonify({"message": "All quizzes created successfully ✅"}), 200

    except Exception as e:
        print("⚠️ Error:", e)
        return jsonify({"error": str(e)}), 500

    finally:
        if 'cursor' in locals(): cursor.close()
        if 'conn' in locals(): conn.close()

@quiz_bp.route('/api/quiz/created', methods=['POST'])
def get_created_quizzes():
    data = request.get_json()
    teacher_id = data.get('teacher_id')

    print("📨 Received request:", data)
    print("🔍 teacher_id:", teacher_id)

    if not teacher_id:
        return jsonify({"error": "teacher_id is required"}), 400

    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("""
            SELECT id, session_id, question, type, is_active
            FROM quizzes
            WHERE teacher_id = %s
            ORDER BY created_at DESC
        """, (teacher_id,))
        quizzes = cursor.fetchall()
        print("🧪 Cevap verilecek quiz sayısı:", len(quizzes))

        return jsonify([
            {**quiz, "is_active": bool(quiz["is_active"])} for quiz in quizzes
        ]), 200


    except Exception as e:
        return jsonify({"error": str(e)}), 500

    finally:
        cursor.close()
        conn.close()

@quiz_bp.route("/api/session/toggle", methods=["POST"])
def toggle_session_status():
    data = request.get_json()
    session_id = data.get("session_id")
    is_active = data.get("is_active")

    if session_id is None or is_active is None:
        return jsonify({"error": "session_id and is_active required"}), 400

    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE sessions SET is_active = %s WHERE id = %s", (is_active, session_id))
        conn.commit()
        return jsonify({"message": f"Session {session_id} updated"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()



@quiz_bp.route('/api/quiz/active_all', methods=['POST'])
def get_all_active_quizzes():
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("""
            SELECT q.id, q.session_id, q.question, q.type, q.options
            FROM quizzes q
            JOIN sessions s ON q.session_id = s.id
            WHERE s.is_active = TRUE
            ORDER BY q.created_at

        """)
        quizzes = cursor.fetchall()

        for q in quizzes:
            q["options"] = json.loads(q["options"])

        return jsonify(quizzes), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

    finally:
        cursor.close()
        conn.close()

@quiz_bp.route('/api/quiz/session/active', methods=['POST'])
def get_all_active_quizzes_by_session():
    data = request.get_json()
    session_id = data.get('session_id')

    if not session_id:
        return jsonify({"error": "session_id is required"}), 400

    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("""
            SELECT id, question, type, options
            FROM quizzes
            WHERE session_id = %s
            ORDER BY created_at ASC
        """, (session_id,))
        quizzes = cursor.fetchall()

        for quiz in quizzes:
            quiz["options"] = json.loads(quiz["options"])

        return jsonify(quizzes), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

    finally:
        cursor.close()
        conn.close()
