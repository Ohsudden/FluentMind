from fastapi import FastAPI, Request, Form, HTTPException, UploadFile, File
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from starlette.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware
from pydantic import BaseModel
from phoenix_tracking import PhoenixTracking
from database import Database
from pwdlib import PasswordHash
import os, time, secrets, ast, json, re
from typing import List, Optional
import requests
from dotenv import load_dotenv
from phoenix.client import Client


load_dotenv()

db = Database()
db.init_db()
app = FastAPI()

phoenix_tracker = PhoenixTracking(app_name="FluentMind")

app.add_middleware(SessionMiddleware, secret_key="dev-secret")

app.mount("/static", StaticFiles(directory="static"), name="static")

templates = Jinja2Templates(directory="static")

@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    return templates.TemplateResponse(request, "index.html")

@app.get("/learn", response_class=HTMLResponse)
async def learn(request: Request, exam: str = None):
    level = request.session.get("proficiency_level")
    user_id = request.session.get("user_id")

    if not level and user_id:
        user = db.get_user_by_id(user_id)
        if user and user.get("proficiency_level"):
             level = user["proficiency_level"]
             request.session["proficiency_level"] = level

    if level:
        return templates.TemplateResponse(request, "learning_dashboard.html", {"request": request, "level": level})
    if exam and exam != "current":
        try:
            test_id = int(exam)
            test_data = db.get_test(test_id)
            if test_data and test_data["test_html"]:
                 return templates.TemplateResponse(request, "level_confirmation.html", {
                    "request": request, 
                    "exam_content": test_data["test_html"],
                    "test_id": test_id
                })
        except ValueError:
            pass

    if exam == "current" and "exam_content" in request.session:
        return templates.TemplateResponse(request, "level_confirmation.html", {
            "request": request, 
            "exam_content": request.session["exam_content"],
            "test_id": "session" 
        })

    if not level:
        return templates.TemplateResponse(request, "level_confirmation.html", {"request": request})
    else:
        return templates.TemplateResponse(request, "learning_dashboard.html", {"request": request, "level": level})


@app.get("/pricing", response_class=HTMLResponse)
async def pricing(request: Request):
    return templates.TemplateResponse(request, "pricing.html")

@app.get("/contacts", response_class=HTMLResponse)
async def contacts(request: Request):
    return templates.TemplateResponse(request, "contacts.html")

@app.get("/registration", response_class=HTMLResponse)
async def registration(request: Request):
    user_id = request.session.get("user_id")
    if user_id:
        return RedirectResponse(url=f"/settings/{user_id}", status_code=302)
    return templates.TemplateResponse(request, "registration.html")

@app.get("/settings", response_class=HTMLResponse)
async def settings_me(request: Request):
    user_id = request.session.get("user_id")
    if not user_id:
        return RedirectResponse(url="/login", status_code=302)
    user = db.get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return templates.TemplateResponse(request, "settings.html", {"userid": user_id, "user": user})

@app.get("/settings/{userid}", response_class=HTMLResponse)
async def settings(request: Request, userid: int):
    user_id = request.session.get("user_id")
    if not user_id:
        return RedirectResponse(url="/login", status_code=302)
    if user_id != userid:
        return RedirectResponse(url=f"/settings/{user_id}", status_code=302)
    user = db.get_user_by_id(userid)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return templates.TemplateResponse(request, "settings.html", {"userid": userid, "user": user})


@app.get("/vocabulary", response_class=HTMLResponse)
async def vocabulary_page(request: Request):
    user_id = request.session.get("user_id")
    if not user_id:
        return RedirectResponse(url="/login", status_code=302)

    user = db.get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return templates.TemplateResponse(request, "vocabulary.html", {"user": user})

@app.post("/api/register")
async def register_user(
    name: str = Form(...),
    surname: str = Form(...),
    email: str = Form(...),
    password: str = Form(...)
):
    success, message = db.create_user(name, surname, email, password)
    
    if success:
        return JSONResponse(status_code=200, content={"success": True, "message": message})
    else:
        return JSONResponse(status_code=400, content={"success": False, "message": message})

@app.get("/login", response_class=HTMLResponse)
async def login(request: Request):
    user_id = request.session.get("user_id")
    if user_id:
        return RedirectResponse(url=f"/settings/{user_id}", status_code=302)
    return templates.TemplateResponse(request, "login.html")

@app.post("/api/login")
async def api_login(
    request: Request,
    email: str = Form(...),
    password: str = Form(...)
):
    success, user_data = db.login_user(email, password)


    if not success:
        return JSONResponse(status_code=401, content={"success": False, "message": user_data})

    request.session["user_email"] = user_data["email"]
    request.session["user_id"] = user_data["id"]

    full_user = db.get_user_by_id(user_data["id"])
    if full_user:
        request.session["proficiency_level"] = full_user.get("proficiency_level")

    return RedirectResponse(url=f"/settings/{user_data['id']}", status_code=302)


@app.get("/api/session")
async def session_info(request: Request):
    return {
        "user_id": request.session.get("user_id"),
        "user_email": request.session.get("user_email"),
    }


def _ensure_authenticated(request: Request):
    user_id = request.session.get("user_id")
    if not user_id:
        raise HTTPException(status_code=401, detail="Not authenticated.")
    return user_id




@app.get("/api/vocabulary")
async def api_get_vocabulary(request: Request):
    try:
        user_id = _ensure_authenticated(request)
    except HTTPException as exc:
        return JSONResponse(status_code=exc.status_code, content={"success": False, "message": exc.detail})

    words = db.get_vocabulary_by_user(user_id)
    return JSONResponse(status_code=200, content={"success": True, "words": words})

@app.post("/api/vocabulary")
async def api_add_word(request: Request):
    try:
        user_id = _ensure_authenticated(request)
    except HTTPException as exc:
        return JSONResponse(status_code=exc.status_code, content={"success": False, "message": exc.detail})

    payload = await request.json()
    word = payload.get("word", "").strip()
    definition = payload.get("definition", "").strip()

    if not word or not definition:
        return JSONResponse(status_code=400, content={"success": False, "message": "Word and definition are required."})

    words = db.get_vocabulary_by_user(user_id)
    words[word] = definition
    db.save_vocabulary_by_user(user_id, words)

    return JSONResponse(status_code=200, content={"success": True, "words": words, "message": "Word saved."})


@app.delete("/api/vocabulary")
async def api_delete_word(request: Request):
    try:
        user_id = _ensure_authenticated(request)
    except HTTPException as exc:
        return JSONResponse(status_code=exc.status_code, content={"success": False, "message": exc.detail})

    payload = await request.json()
    word = payload.get("word", "").strip()

    if not word:
        return JSONResponse(status_code=400, content={"success": False, "message": "Word is required."})

    words = db.get_vocabulary_by_user(user_id)

    if word not in words:
        return JSONResponse(status_code=404, content={"success": False, "message": "Word not found."})

    del words[word]
    db.save_vocabulary_by_user(user_id, words)

    return JSONResponse(status_code=200, content={"success": True, "words": words, "message": "Word deleted."})

@app.post("/api/change-password")
async def change_password(request: Request,
    old_password: str = Form(...),
    new_password: str = Form(...)
):
    user_id = request.session.get("user_id")
    if not user_id:
        return JSONResponse(status_code=401, content={"success": False, "message": "Not authenticated."})

    user = db.get_user_by_id(user_id)
    if not user:
        return JSONResponse(status_code=404, content={"success": False, "message": "User not found."})

    stored_hash = user['password_hash']
    if not PasswordHash.recommended().verify(old_password, stored_hash):
        return JSONResponse(status_code=400, content={"success": False, "message": "Incorrect old password."})

    db.rechange_password(user_id, new_password)

    return JSONResponse(status_code=200, content={"success": True, "message": "Password changed successfully."})

@app.post("/api/upload-certificate")
async def cloud_certificate(request: Request, file: UploadFile = File(...)):
    user_id = request.session.get("user_id")
    if not user_id:
        return JSONResponse(status_code=401, content={"success": False, "message": "Not authenticated."})

    allowed_ext = {"pdf", "jpg", "jpeg", "png"}
    filename = file.filename or "certificate"
    ext = filename.rsplit('.', 1)[-1].lower() if '.' in filename else ''
    if ext not in allowed_ext:
        return JSONResponse(status_code=400, content={"success": False, "message": "Unsupported file type."})
    
    cert_dir = os.path.join(os.getcwd(), "static", "certificates")
    os.makedirs(cert_dir, exist_ok=True)

    safe_name = os.path.basename(filename)
    dest_path = os.path.join(cert_dir, safe_name)

    contents = await file.read()
    with open(dest_path, 'wb') as f:
        f.write(contents)

    rel_path = f"certificates/{safe_name}"
    db.upload_certificate(user_id, rel_path)

    static_url = f"/static/{rel_path}"
    return JSONResponse(status_code=200, content={"success": True, "path": rel_path, "url": static_url, "message": "Certificate uploaded successfully."})

@app.post("/api/upload-image")
async def upload_image_endpoint(request: Request, file: UploadFile = File(...)):
    user_id = request.session.get("user_id")
    if not user_id:
        return JSONResponse(status_code=401, content={"success": False, "message": "Not authenticated."})

    allowed_ext = {"jpg", "jpeg", "png"}
    filename = file.filename or "profile_image"
    ext = filename.rsplit('.', 1)[-1].lower() if '.' in filename else ''
    if ext not in allowed_ext:
        return JSONResponse(status_code=400, content={"success": False, "message": "Unsupported file type."})
    
    image_dir = os.path.join(os.getcwd(), "static", "profile_images")
    os.makedirs(image_dir, exist_ok=True)

    safe_name = os.path.basename(filename)
    dest_path = os.path.join(image_dir, safe_name)

    contents = await file.read()
    with open(dest_path, 'wb') as f:
        f.write(contents)

    rel_path = f"profile_images/{safe_name}"
    db.upload_image(user_id, rel_path)

    static_url = f"/static/profile_images/{safe_name}"
    return JSONResponse(status_code=200, content={"success": True, "path": rel_path, "url": static_url, "message": "Profile image uploaded successfully."})

async def _extract_payload_value(request: Request, key: str):
    content_type = request.headers.get("content-type", "")
    value = None

    if "application/json" in content_type:
        try:
            data = await request.json()
        except Exception:
            data = {}
        value = data.get(key)
        if value is None and "-" in key:
            value = data.get(key.replace("-", "_"))
    else:
        form = await request.form()
        value = form.get(key)
        if value is None and "-" in key:
            value = form.get(key.replace("-", "_"))

    if isinstance(value, str):
        return value.strip()
    return value


@app.post("/api/update-native-language")
async def native_language_changes(request: Request):
    user_id = request.session.get("user_id")
    if not user_id:
        return JSONResponse(status_code=401, content={"success": False, "message": "Not authenticated."})

    native_language = await _extract_payload_value(request, "native_language")
    if not native_language:
        native_language = await _extract_payload_value(request, "native-language")

    if not native_language:
        return JSONResponse(status_code=400, content={"success": False, "message": "Native language is required."})

    db.update_native_language(user_id, native_language)

    return JSONResponse(status_code=200, content={"success": True, "message": "Native language updated successfully."})


@app.post("/api/update-interface-language")
async def interface_language_changes(request: Request):
    user_id = request.session.get("user_id")
    if not user_id:
        return JSONResponse(status_code=401, content={"success": False, "message": "Not authenticated."})

    interface_language = await _extract_payload_value(request, "interface_language")
    if not interface_language:
        interface_language = await _extract_payload_value(request, "interface-language")

    if not interface_language:
        return JSONResponse(status_code=400, content={"success": False, "message": "Interface language is required."})

    db.update_interface_language(user_id, interface_language)

    return JSONResponse(status_code=200, content={"success": True, "message": "Interface language updated successfully."})

@app.post("/api/update-email")
async def email_changes(request: Request):
    user_id = request.session.get("user_id")
    if not user_id:
        return JSONResponse(status_code=401, content={"success": False, "message": "Not authenticated."})

    email = await _extract_payload_value(request, "email")

    if not email:
        return JSONResponse(status_code=400, content={"success": False, "message": "Email is required."})

    db.update_email(user_id, email)

    return JSONResponse(status_code=200, content={"success": True, "message": "Email updated successfully."})


@app.get("/api/generate-exam")
async def generate_exam(request: Request):
    user_id = request.session.get("user_id")
    if not user_id:
        return JSONResponse(status_code=401, content={"success": False, "message": "Not authenticated."})

    try:
        generation_result = phoenix_tracker.generate(
            temperature=1.0,
            top_p=0.9,
            max_tokens=2000,
            model="gemini-2.5-flash-preview-09-2025",
            prompt_context="""You are an expert English exam creator. Generate a 30-question multiple-choice English placement test.
            
            IMPORTANT: Return ONLY a valid JSON object. Do NOT include any introductory text, markdown formatting (like ```json), or explanations. The output must be parseable by JSON.parse().
            
            The JSON structure MUST be:
            {
                "questions": [
                    {
                        "id": 1,
                        "question": "Question text here",
                        "options": {
                            "A": "Option A text",
                            "B": "Option B text",
                            "C": "Option C text",
                            "D": "Option D text"
                        }
                    }
                ]
            }
            
            Ensure the questions cover a range of difficulty levels (A1 to C2) to assess proficiency accurately.
            JSON ONLY.""", name="English Exam", type="exam", collection_name="CefrGrammarProfile")
        test_id = db.create_pending_test(user_id, generation_result["content"])
        return JSONResponse(status_code=200, content={"success": True, "exam": {"id": test_id}})
    except Exception as e:
        print(f"Error generating exam: {e}")
        return JSONResponse(status_code=500, content={"success": False, "message": str(e)})

@app.post("/api/submit-exam")
async def submit_exam(request: Request):
    user_id = request.session.get("user_id")
    if not user_id:
        return JSONResponse(status_code=401, content={"success": False, "message": "Not authenticated."})

    payload = await request.json()
    exam_answers = payload.get("exam_answers", "")
    test_id_val = payload.get("test_id")

    if not exam_answers:
        return JSONResponse(status_code=400, content={"success": False, "message": "Exam answers are required."})
    
    exam_content = ""
    if test_id_val and str(test_id_val) != "session":
        try:
            test_data = db.get_test(int(test_id_val))
            if test_data:
                exam_content = test_data["test_html"]
        except Exception:
            pass

    if not exam_content:
        exam_content = request.session.get("exam_content", "")
    
    english_test_check_propmt = f"""You are an expert English tutor. Provide an English level based on the student's answers to the exam below. 
    Write only one of CEFR levels (A1, A2, B1, B2, C1, C2) as the response.
    
    Here is the exam questions:
    {exam_content}
    
    Here is the student's answers:
    {exam_answers}
    """
    feedback_result = phoenix_tracker.generate(
        temperature=0.2,
        top_p=0.5,
        max_tokens=2000,
        model="gemini-2.5-flash-preview-09-2025",
        prompt_context=english_test_check_propmt
    )
    feedback = feedback_result["content"]
    run_id = feedback_result["run_id"]

    if test_id_val and str(test_id_val) != "session":
        try:
            db.update_test_submission(
                test_id=int(test_id_val),
                submitted_answers_json=exam_answers,
                assessed_level=feedback,
                assessed_by_model="gemini-2.5-flash-preview-09-2025",
                phoenix_run_id=run_id
            )
        except Exception as e:
            print(f"Error updating test: {e}")
    else:
        db.add_test(
            user_id=user_id,
            test_html=request.session.get("exam_content", ""),
            submitted_answers_json=exam_answers,
            assessed=True,
            assessed_level=feedback,
            assessed_by_model="gemini-2.5-flash-preview-09-2025",
            phoenix_run_id=run_id
        )
    db.update_english_level(user_id, feedback)
    return JSONResponse(status_code=200, content={"success": True, "feedback": feedback})

@app.post("/api/generate-course")
async def generate_course(request: Request, level: str):
    user_id = request.session.get("user_id")
    if not user_id:
        return JSONResponse(status_code=401, content={"success": False, "message": "Not authenticated."})
    response = phoenix_tracker.generate(
        temperature=0.7,
        top_p=0.9,
        max_tokens=3000,
        model="gemini-2.5-flash-preview-09-2025",
        prompt_context=f"""You are an expert English course creator. Create a detailed 8-week English course for a student at {level} level. 
        IMPORTANT: Return ONLY a valid JSON object. Do NOT include any introductory text, markdown formatting (like ```json), or explanations. The output must be parseable by JSON.parse(). The JSON structure MUST be:
        {{
            "title": "Course Title",
            "description": "Brief description of the course",
            "duration_weeks": 8,
            "course_plan": [
                {{
                    "module": 1,
                    "topics": ["Topic 1", "Topic 2"],
                    "objectives": ["Objective 1", "Objective 2"],
                    "activities": ["Activity 1", "Activity 2"]
                }}
            ]
        }}
        Ensure the course is engaging and covers all essential skills: reading, writing, speaking.
        JSON ONLY.""", name="English Course", type="course", collection_name="CefrGrammarProfile")
    
    course_content = response["content"]
    if isinstance(course_content, str):
        import json
        import re
        import ast
        try:
            to_parse = course_content.strip()
            match = re.search(r"\{.*\}", to_parse, re.DOTALL)
            if match:
                to_parse = match.group(0)
            
            if to_parse.startswith("```"):
                parts = to_parse.split("\n", 1)
                if len(parts) > 1:
                    to_parse = parts[1]
                to_parse = to_parse.strip()
                if to_parse.endswith("```"):
                     to_parse = to_parse[:-3]

            try:
                course_content = json.loads(to_parse)
            except json.JSONDecodeError:
                 course_content = ast.literal_eval(to_parse)

        except Exception as e:
            print(f"Error parsing course content JSON: {e}")
            print(f"Raw content start: {course_content[:500]}...")
            print(f"Raw content end: ...{course_content[-500:]}")
            return JSONResponse(status_code=500, content={"success": False, "message": f"Failed to parse course content from LLM: {str(e)}"})

    if not isinstance(course_content, dict):
         return JSONResponse(status_code=500, content={"success": False, "message": "Course content is not a valid dictionary."})

    course_id = db.add_course(level=level, title=course_content.get('title'), description=course_content.get('description'), 
                  duration_weeks=course_content.get('duration_weeks'), course_plan=str(course_content.get('course_plan')))

    start_date = time.strftime("%Y-%m-%d")
    db.enroll_user_in_course(user_id=user_id, course_id=course_id, start_date=start_date)

    return JSONResponse(status_code=200, content={"success": True, "course": course_content})


class ExerciseSubmission(BaseModel):
    id: int
    question_context: str
    user_answer: str

class ModuleSubmission(BaseModel):
    url: str
    exercises: List[ExerciseSubmission]

@app.post("/api/submit_module_answers")
async def submit_module_answers(submission: ModuleSubmission, request: Request):
    user_id = request.session.get("user_id")
    if not user_id:
        return JSONResponse(status_code=401, content={"success": False, "message": "Not authenticated."})
    
    # Parse URL to get course and module info
    course_id_match = re.search(r'course(\d+)', submission.url)
    module_num_match = re.search(r'module(\d+)', submission.url)
    
    course_id = course_id_match.group(1) if course_id_match else "unknown"
    module_number = module_num_match.group(1) if module_num_match else "unknown"

    exercises_text = ""
    for ex in submission.exercises:
        exercises_text += f"Exercise {ex.id}:\nContext: {ex.question_context}\nUser Answer: {ex.user_answer}\n\n"

    prompt = f"""
    You are an expert English teacher grading a student's module submission.
    
    Course ID: {course_id}
    Module: {module_number}
    
    Here are the exercises and the student's answers extracted from the page:
    {exercises_text}
    
    Please provide constructive feedback for the student. 
    1. Correct any mistakes politely.
    2. Explain why an answer is wrong if it is.
    3. Praise good answers.
    4. Provide the correct answer if the student was wrong.
    
    Format your response as HTML (just the inner body content, no <html> tags) suitable for displaying inside a div. 
    Use <div class="feedback-item"> for each exercise feedback.
    Add some styling classes.
    """

    response = phoenix_tracker.generate(
        temperature=0.3,
        model="gemini-2.5-flash-preview-09-2025",
        prompt_context=prompt,
        name="Module Grading",
        type="grading", 
        collection_name="CefrGrammarProfile"
    )

    feedback_html = response["content"] # phoenix_tracker returns dict
    
    # Handle occasional markdown wrapping
    if isinstance(feedback_html, str) and feedback_html.strip().startswith("```html"):
         feedback_html = feedback_html.strip().split("\n", 1)[1].rsplit("\n", 1)[0]
    
    return JSONResponse(status_code=200, content={"success": True, "feedback_html": feedback_html})

@app.get("/api/get_courses")
async def get_courses(request: Request):
    user_id = request.session.get("user_id")
    if not user_id:
        return JSONResponse(status_code=401, content={"success": False, "message": "Not authenticated."})
    courses = db.get_user_courses(user_id)
    return JSONResponse(status_code=200, content={"success": True, "courses": courses})

@app.get("/api/generate-module")
async def generate_module(request: Request, course_id: int, module_number: int):
    user_id = request.session.get("user_id")
    if not user_id:
        return JSONResponse(status_code=401, content={"success": False, "message": "Not authenticated."})
    content = db.get_module_content(module_number, course_id)
    if content:
        return JSONResponse(status_code=200, content={"success": True, "module": content})
    course =db.get_course_by_id(course_id)
    course_plan = course.get("course_plan", "")
    response = phoenix_tracker.generate(
        temperature=0.7,
        top_p=0.9,
        max_tokens=2000,
        model="gemini-2.5-flash-preview-09-2025",
        prompt_context=f"""You are an expert English course module creator. Create a detailed module {module_number} for the following course plan:
        {course_plan}
        IMPORTANT: Return ONLY a valid JSON object. Do NOT include any introductory text, markdown formatting (like ```json), or explanations. In JSON format, provide:
        HTML content for module {module_number} including lessons, exercises, and resources. The output must be parseable by JSON.parse(). Use consistent formatting and html classes for easy rendering. 
        Each exercise should have clear instructions and answer sections.

        For exercises requiring user input, use the following HTML structure and classes:
        - For text inputs: use <input type="text" class="exercise-input" placeholder="...">
        - For longer text inputs (writing prompts): use <textarea class="exercise-input" rows="4" placeholder="..."></textarea>
        - For multiple choice/radio buttons: wrap each option in a label with class "exercise-radio-label". Inside the label, put the <input type="radio" class="exercise-radio-input" name="group_name"> first, then the text. Wrap the group of radio buttons in a div with class "exercise-radio-group".
        - Wrap each exercise in a div with class "exercise-box".

        Ensure the JSON output is a single valid JSON string. Do not use Python-style string concatenation (e.g. "..." + "...") inside values.
        JSON ONLY.""", name="English Course Module", type="course_module", collection_name="CefrGrammarProfile")
    module_content = response["content"]
    phoenix_run_id = response.get("run_id")
    
    parsed_json = None
    if isinstance(module_content, str):
        content_to_parse = module_content.strip()
        
        code_block_match = re.search(r"```(?:json)?\s*(.*?)```", content_to_parse, re.DOTALL)
        if code_block_match:
            content_to_parse = code_block_match.group(1).strip()
        
        try:
            parsed_json = json.loads(content_to_parse)
        except json.JSONDecodeError:
            try:
                start = content_to_parse.find('{')
                end = content_to_parse.rfind('}')
                if start != -1 and end != -1:
                    json_str = content_to_parse[start:end+1]
                    parsed_json = json.loads(json_str)
            except:
                pass

        if parsed_json is None:
             print(f"Error parsing module content JSON. Raw content preview: {module_content[:200]}")
             if "<div" in module_content or "<h" in module_content:
                 parsed_json = {"html": module_content}
    
    if parsed_json:
        module_content = parsed_json
        
    db.add_module(course_id=course_id, title=f"Module {module_number}", week_number=module_number, content_html=str(module_content), phoenix_id=phoenix_run_id)
    return JSONResponse(status_code=200, content={"success": True, "module": module_content})

@app.get("/learn/course{course_id}")
async def learn_course(request: Request, course_id: int):
    user_id = request.session.get("user_id")
    if not user_id:
        return RedirectResponse(url="/login", status_code=302)

    course = db.get_course_by_id(course_id)
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    modules = db.get_modules_by_course(course_id)

    return templates.TemplateResponse(request, "course_learning.html", {
        "request": request,
        "course": course,
        "modules": modules
    })

@app.get("/learn/course{course_id}/module{module_number}")
async def learn_course_module(request: Request, course_id: int, module_number: int):
    user_id = request.session.get("user_id")
    if not user_id:
        return RedirectResponse(url="/login", status_code=302)

    course = db.get_course_by_id(course_id)
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    
    modules = db.get_modules_by_course(course_id)
    current_module = next((m for m in modules if m["week_number"] == module_number), None)
    
    if not current_module:
         pass

    if current_module and current_module.get("content_html"):
        try:
            import ast
            content_data = None
            raw_content = current_module["content_html"]
            
            try:
                # Attempt to clean up common issues like Python string concatenation
                cleaned_raw = raw_content
                if '" + "' in cleaned_raw or "' + '" in cleaned_raw:
                    cleaned_raw = re.sub(r'"\s*\+\s*"', "", cleaned_raw)
                    cleaned_raw = re.sub(r"'\s*\+\s*'", "", cleaned_raw)
                    
                content_data = json.loads(cleaned_raw)
            except:
                try:
                    cleaned = raw_content.strip()
                    # Try cleaning concatenation here too
                    cleaned = re.sub(r'"\s*\+\s*"', "", cleaned)
                    cleaned = re.sub(r"'\s*\+\s*'", "", cleaned)
                    
                    if cleaned.startswith('{') and cleaned.endswith('"'):
                        cleaned = cleaned[:-1]
                    content_data = json.loads(cleaned)
                except:
                    try:
                        content_data = ast.literal_eval(raw_content)
                    except:
                        pass
            
            if isinstance(content_data, dict):

                 current_module["rendered_html"] = ""
                 if "html" in content_data:
                     current_module["rendered_html"] += content_data["html"]
                 elif "content" in content_data:
                      current_module["rendered_html"] += str(content_data["content"])
                 else:

                     for k, v in content_data.items():
                         if isinstance(v, list):
                             current_module["rendered_html"] += f"<h3>{k.capitalize().replace('_', ' ')}</h3><ul>"
                             for item in v:
                                 current_module["rendered_html"] += f"<li>{item}</li>"
                             current_module["rendered_html"] += "</ul>"
                         elif isinstance(v, str):
                             if v.strip().startswith("<"):
                                 current_module["rendered_html"] += v
                             else:
                                 current_module["rendered_html"] += f"<p><strong>{k}:</strong> {v}</p>"
            elif isinstance(content_data, str):
                 current_module["rendered_html"] = content_data
            else:
                 # Fallback: parsing failed, treat raw content as HTML
                 current_module["rendered_html"] = raw_content

        except Exception as e:
            print(f"Error preparing module content: {e}")
            current_module["rendered_html"] = "Error loading content."

    return templates.TemplateResponse(request, "course_module.html", {
        "request": request,
        "course": course,
        "module": current_module,
        "module_number": module_number
    })

@app.post("/api/get-modules")
async def api_get_modules(request: Request, course_id: int):
    user_id = request.session.get("user_id")
    if not user_id:
        return JSONResponse(status_code=401, content={"success": False, "message": "Not authenticated."})
        
    db_modules = db.get_modules_by_course(course_id)
    created_map = {m['week_number']: m for m in db_modules}
    
    final_modules = []
    
    course = db.get_course_by_id(course_id)
    if course and course.get("course_plan"):
        try:
            plan_str = course["course_plan"]
            if isinstance(plan_str, str):
                try:
                    plan_list = ast.literal_eval(plan_str)
                except:
                    plan_list = json.loads(plan_str)
            else:
                plan_list = plan_str

            if isinstance(plan_list, list):
                for item in plan_list:
                    week_num = item.get('module')
                    
                    if week_num in created_map:
                        db_mod = created_map[week_num]
                        final_modules.append({
                             "module_id": db_mod["module_id"],
                             "course_id": course_id,
                             "title": db_mod["title"],
                             "week_number": week_num,
                             "content_html": json.dumps(item) 
                        })
                    else:
                        final_modules.append({
                             "module_id": f"plan_{week_num}",
                             "course_id": course_id,
                             "title": item.get('title', f"Module {week_num}"),
                             "week_number": week_num,
                             "content_html": json.dumps(item)
                        })
            else:
                final_modules = db_modules
        except Exception as e:
            print(f"Error parsing course plan in mix: {e}")
            final_modules = db_modules
    else:
        final_modules = db_modules

    return JSONResponse(status_code=200, content={"success": True, "modules": final_modules})

# @app.post("/v1/span_annotations")
# async def span_annotations(request: Request):
#     payload = await request.json()
#     span_id = payload.get("span_id")
#     annotations = payload.get("annotations", {})
    
#     try:
#         if span_id:
#             try:
#                 client = Client()
#                 client.add_span_annotations(
#                     annotation_name="user feedback",
#                     annotator_kind="HUMAN",
#                     span_id=span_id,
#                     label=annotations.get("review"),
#                     score=annotations.get("score"),
#                 )
#             except Exception as e:
#                 print(f"Phoenix annotation failed (ignoring): {e}")

#         db.assess_module_user(
#             user_id=request.session.get("user_id"),
#             module_id=annotations.get("module_id"),
#             course_id=annotations.get("course_id"),
#             rating=annotations.get("score"),
#             review=annotations.get("review"),
#         )
#         return JSONResponse(status_code=200, content={"success": True, "message": "Feedback submitted."})
#     except Exception as e:
#         return JSONResponse(status_code=500, content={"success": False, "message": str(e)})

@app.post("/api/submit-module-feedback")
async def submit_module_feedback(request: Request):
    user_id = request.session.get("user_id")
    if not user_id:
        return JSONResponse(status_code=401, content={"success": False, "message": "Not authenticated."})

    try:
        payload = await request.json()
    except Exception:
        return JSONResponse(status_code=400, content={"success": False, "message": "Invalid JSON."})
    
    if "annotations" not in payload:
         return JSONResponse(status_code=400, content={"success": False, "message": "Annotations missing."})

    annotations = payload.get("annotations", {})
    span_id = payload.get("span_id")
    
    try:
        db.assess_module_user(
            user_id=user_id,
            module_id=annotations.get("module_id"),
            course_id=annotations.get("course_id"),
            rating=annotations.get("score"),
            review=annotations.get("review"),
        )
        print(f"[✓] Feedback stored in database for user {user_id}, module {annotations.get('module_id')}")
        
        if span_id and span_id != "None" and span_id.strip():
            print(f"[INFO] Attempting to annotate Phoenix span: {span_id}")
            try:
                phoenix_host = os.getenv("PHOENIX_HOST", "http://localhost:6006")
                url = f"{phoenix_host}/v1/span_annotations?sync=false"
                
                annotation = {
                    "span_id": span_id,
                    "name": "user feedback",
                    "annotator_kind": "HUMAN",
                    "result": {
                        "label": annotations.get("review"),
                        "score": annotations.get("score"),
                    }
                }
                
                response = requests.post(url, json={"data": [annotation]})
                
                if response.status_code == 200:
                    print(f"[✓] Annotation added to Phoenix successfully via REST API")
                else:
                    print(f"[WARNING] Phoenix annotation failed with status {response.status_code}: {response.text}")

            except Exception as e:
                print(f"[WARNING] Phoenix annotation failed (feedback still saved): {type(e).__name__}: {str(e)}")
        else:
            print(f"[WARNING] No valid span_id provided. Feedback saved but not annotated in Phoenix.")
        
        return JSONResponse(status_code=200, content={"success": True, "message": "Feedback submitted and saved."})
    except Exception as e:
        print(f"[ERROR] Failed to save feedback: {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()
        return JSONResponse(status_code=500, content={"success": False, "message": f"Error saving feedback: {str(e)}"})


@app.post("/api/submit-module-progress")
async def submit_module_progress(request: Request):
    user_id = request.session.get("user_id")
    if not user_id:
        return JSONResponse(status_code=401, content={"success": False, "message": "Not authenticated."})

    try:
        payload = await request.json()
    except Exception:
        return JSONResponse(status_code=400, content={"success": False, "message": "Invalid JSON."})

    module_id = payload.get("module_id")
    course_id = payload.get("course_id")
    answers = payload.get("answers")

    if not module_id or not course_id:
         return JSONResponse(status_code=400, content={"success": False, "message": "Missing module_id or course_id."})

    module_content_html = db.get_module_content(module_id, course_id)
    
    context_str = module_content_html if module_content_html else "Content not available from DB."
    answer_str = json.dumps(answers)

    prompt = f"""You are an expert English tutor. Grade the student's progress on the following module exercises.
    
    Module Content (HTML):
    {context_str}
    
    Student Answers:
    {answer_str}
    
    Provide:
    1. A score between 0 and 100.
    2. Constructive feedback/comments.
    
    IMPORTANT: Return ONLY a valid JSON object. Do NOT include any introductory text or markdown.
    Structure:
    {{
        "score": 85.5,
        "comments": "Good job! You missed..."
    }}
    JSON ONLY.
    """

    try:
        generation_result = phoenix_tracker.generate(
            temperature=0.0,
            top_p=1.0,
            max_tokens=1000,
            model="gemini-2.5-flash-preview-09-2025",
            prompt_context=prompt,
            name="Module Grading",
            type="grading",
            collection_name="CefrGrammarProfile"
        )
        
        result_content = generation_result["content"]
        run_id = generation_result["run_id"]
        
        assessed_score = 0.0
        comments = "No comments."
        
        try:
            import json
            cleaned = result_content.strip()
            if cleaned.startswith("```"):
                cleaned = cleaned.split("\n", 1)[1].rsplit("\n", 1)[0]
            if cleaned.startswith("json"):
                 cleaned = cleaned[4:]
            
            data = json.loads(cleaned)
            assessed_score = float(data.get("score", 0))
            comments = data.get("comments", "")
        except Exception as e:
            print(f"Error parsing grading response: {e}")
            comments = "Error parsing grading response."
            
        db.add_progress_tracking(
            user_id=user_id,
            module_id=module_id,
            course_id=course_id,
            answers_json=answer_str,
            assessed=True,
            assessed_score=assessed_score,
            assessed_by_model="gemini-2.5-flash-preview-09-2025",
            comments_from_model=comments,
            phoenix_run_id=run_id
        )
        
        return JSONResponse(status_code=200, content={
            "success": True, 
            "score": assessed_score, 
            "comments": comments
        })

    except Exception as e:
        print(f"Error in submit-module-progress: {e}")
        return JSONResponse(status_code=500, content={"success": False, "message": str(e)})