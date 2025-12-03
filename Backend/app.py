from flask import Flask, request, jsonify,send_file
from werkzeug.utils import secure_filename
import os
import io
from FincoachAgents.incomeAnalyser import IncomeAgent
from agents.resume_agent import ResumeParser
from agents.question_roadmapPlanner import InterviewPlanner
from agents.question_fetcher import QuestionFetcher
from agents.feedback_agent import FeedbackAgent
from agents.resume_feedback_agent import ResumeFeedbackAgent
from agents.resume_qna_agent import InteractiveQnAAgent
from agents.cover_letter_gen import CoverLetterGenerator
import json
from typing import Dict, Any
from flask_cors import CORS
import PyPDF2
from io import BytesIO
from agents.murftts import MurfTTS

app = Flask(__name__)
CORS(app)



resume_feedback_agent = ResumeFeedbackAgent()
interactive_qna_agent = InteractiveQnAAgent()
generator = CoverLetterGenerator()

# Configuration
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'pdf'}
murf_api = MurfTTS(api_key="ap2_875ac707-e36c-46a6-af3d-722c2becaa49")

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename: str) -> bool:
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/parse-resume', methods=['POST'])
def parse_resume() -> Dict[str, Any]:
    """Endpoint to handle resume PDF upload and parsing."""
    # Check if the post request has the file part
    if 'resume' not in request.files:
        return jsonify({'error': 'No file part in the request'}), 400

    file = request.files['resume']

    # If user does not select file, browser might submit an empty part without filename
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    if file and allowed_file(file.filename):
        try:
            # Secure the filename and save the file
            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)

            # Parse the resume
            parser = ResumeParser()
            result = parser.parse_resume(file_path)

            # Clean up: remove the saved file
            os.remove(file_path)

            return jsonify(result)

        except Exception as e:
            # Clean up in case of error
            if os.path.exists(file_path):
                os.remove(file_path)
            return jsonify({'error': str(e)}), 500

    return jsonify({'error': 'File type not allowed. Only PDF files are accepted.'}), 400

@app.route("/murf-tts", methods=["POST"])
def murf_tts():
    data = request.get_json()

    if not data or "text" not in data:
        return jsonify({"error": "Please provide 'text' in JSON body."}), 400

    text = data["text"]

    # Generate TTS audio
    audio_bytes = murf_api.generate_audio(text)

    if audio_bytes is None:
        return jsonify({"error": "TTS generation failed."}), 500

    # Return audio file as streaming response
    return send_file(
        io.BytesIO(audio_bytes),
        mimetype="audio/mpeg",
        as_attachment=True,
        download_name="tts_audio.mp3"
    )


@app.route('/generate-interview-questions', methods=['POST'])
def generate_interview_questions() -> Dict[str, Any]:
    """Endpoint to generate interview questions based on resume summary and other parameters."""
    try:
        # Get the request data
        data = request.get_json()

        # Validate required fields
        required_fields = ['resume_summary', 'company', 'role', 'round']
        if not all(field in data for field in required_fields):
            return jsonify({
                "error": "Missing required fields",
                "required_fields": required_fields
            }), 400

        # Initialize the interview planner
        planner = InterviewPlanner()

        # Generate interview questions
        result = planner.generate_interview_questions(
            resume_summary=data['resume_summary'],
            company=data['company'],
            role=data['role'],
            round_type=data['round']
        )

        return jsonify(result)

    except json.JSONDecodeError:
        return jsonify({"error": "Invalid JSON format in request"}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500  

@app.route('/get-question', methods=['POST'])
def get_question() -> Dict[str,Any]:
    try:
        data= request.get_json()
        
        if not data:
            return jsonify({"error":"No JSON data provided"}),400
        
        if 'sr_no' not in data or 'interview_plan' not in data:
            return jsonify({
                "error":"Missing required fields",
                "required_fields": ["sr_no", "interview_plan"]
            }),400
            
        question = QuestionFetcher.get_question_by_srno(
            interview_plan= data['interview_plan'],
            sr_no= data['sr_no']
        )
        
        if "error" in question:
            return jsonify(question),404
        
        return jsonify(question)
    
    except json.JSONDecodeError:
        return jsonify({"error": "Invalid JSON format in request"}),400
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# @app.route('/evaluate-answer', methods=['POST'])
# def evaluate_answer() -> Dict[str, Any]:
#     """
#     Endpoint to evaluate a user's interview answer and provide feedback.

#     Expected JSON payload:
#     {
#         "question": "The interview question",
#         "user_answer": "The user's response to the question"
#     }
#     """
#     try:
#         # Get and validate the request data
#         data = request.get_json()

#         if not data:
#             return jsonify({"error": "No JSON data provided"}), 400

#         required_fields = ['question', 'user_answer']
#         if not all(field in data for field in required_fields):
#             return jsonify({
#                 "error": "Missing required fields",
#                 "required_fields": required_fields
#             }), 400

#         # Initialize the feedback agent
#         agent = FeedbackAgent()

#         # Get the evaluation
#         result = agent.evaluate_answer(
#             question=data['question'],
#             user_answer=data['user_answer']
#         )

#         return jsonify(result)

#     except json.JSONDecodeError:
#         return jsonify({"error": "Invalid JSON format in request"}), 400
#     except Exception as e:
#         return jsonify({"error": str(e)}), 500

@app.route('/evaluate-answer', methods=['POST'])
def evaluate_answer() -> Dict[str, Any]:
    """
    Endpoint to evaluate a user's interview answer and provide feedback.

    Expected JSON payload:
    {
        "question": "The interview question",
        "user_answer": "The user's response to the question",
        "resume_summary": "The summary from the user's resume"
    }
    """
    try:
        data = request.get_json()

        if not data:
            return jsonify({"error": "No JSON data provided"}), 400

        required_fields = ['question', 'user_answer', 'resume_summary']
        if not all(field in data for field in required_fields):
            return jsonify({
                "error": "Missing required fields",
                "required_fields": required_fields
            }), 400

        agent = FeedbackAgent()
        result = agent.evaluate_answer(
            question=data['question'],
            user_answer=data['user_answer'],
            resume_summary=data['resume_summary']
        )

        return jsonify(result)

    except json.JSONDecodeError:
        return jsonify({"error": "Invalid JSON format in request"}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# Resume Agent Code
# ############################

# @app.route('/evaluate-resume', methods=['POST'])
# def evaluate_resume():
#     # Get the resume text from the request
#     data = request.get_json()
#     resume_text = data.get('resume_text', '')

#     # Use the Resume Feedback Agent to evaluate the resume
#     feedback = resume_feedback_agent.evaluate_resume(resume_text)

#     # Return the feedback as a JSON response
#     return jsonify(feedback)

@app.route('/evaluate-resume', methods=['POST'])
def evaluate_resume():
    # Check if the post request has the file part
    if 'resume_pdf' not in request.files:
        return jsonify({"error": "No file part"}), 400

    file = request.files['resume_pdf']

    # If the user does not select a file, the browser submits an empty file without a filename
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    if file:
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)

        # Use the Resume Feedback Agent to evaluate the resume
        feedback = resume_feedback_agent.evaluate_resume(filepath)

        # Optionally, remove the file after processing
        os.remove(filepath)

        # Return the feedback as a JSON response
        return jsonify(feedback)


@app.route('/answer-resumeQuestion', methods=['POST'])
def answer_question():
    # Get the question and resume text from the request
    data = request.get_json()
    question = data.get('question', '')
    resume_text = data.get('resume_text', '')

    # Use the Interactive Q&A Agent to answer the question
    answer = interactive_qna_agent.answer_question(question, resume_text)

    # Return the answer as a JSON response
    return jsonify(answer)

@app.route("/generate_cover_letter", methods=["POST"])
def generate_cover_letter():
    try:
        # Check if resume file and job description are provided
        if 'resume' not in request.files or 'jd' not in request.form:
            return jsonify({"error": "Resume file and job description are required"}), 400
        
        resume_file = request.files['resume']
        jd = request.form['jd']

        # Validate file type
        if not resume_file.filename.endswith('.pdf'):
            return jsonify({"error": "Resume must be a PDF file"}), 400

        # Read the uploaded PDF file
        pdf_file = BytesIO(resume_file.read())
        pdf_reader = PyPDF2.PdfReader(pdf_file)
        
        resume_text = ""
        for page in pdf_reader.pages:
            resume_text += page.extract_text() + "\n"
        
        # Generate cover letter
        cover_letter = generator.generate(resume_text, jd)
        
        return jsonify({"cover_letter": cover_letter})
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/analyze-income', methods=['POST'])
def analyze_income() -> Dict[str, Any]:
    """Analyze multiple income sources and return insights."""
    try:
        data = request.get_json()

        # Validation
        if 'income' not in data or not isinstance(data['income'], list):
            return jsonify({
                "error": "Missing required field: 'income' must be a list of objects"
            }), 400

        agent = IncomeAgent()

        result = agent.analyze_income(data)

        return jsonify(result)

    except json.JSONDecodeError:
        return jsonify({"error": "Invalid JSON format in request"}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500



@app.route('/health', methods=['GET'])
def health_check() -> Dict[str, str]:
    """Health check endpoint."""
    return jsonify({'status': 'healthy'})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)


