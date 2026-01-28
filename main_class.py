from fastapi import FastAPI, Request, Form, HTTPException, UploadFile, File
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from starlette.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware
from phoenix_tracking import PhoenixTracking
from database import Database
from pwdlib import PasswordHash
import os, time, secrets, ast, json, re
from typing import List, Optional
import requests
from dotenv import load_dotenv
from phoenix.client import Client

class FluentMindApp:
    def __init__(self):
        load_dotenv()
        self.app = FastAPI()
        self.setup_services()
        self.setup_middleware()
        self.setup_routes()

    def setup_services(self):
        self.db = Database()
        self.db.init_db()
        self.phoenix_tracker = PhoenixTracking(app_name="FluentMind")
        self.app.mount("/static", StaticFiles(directory="static"), name="static")
        self.templates = Jinja2Templates(directory="static")

    def setup_middleware(self):
        self.app.add_middleware(SessionMiddleware, secret_key="dev-secret")

    def setup_routes(self):
        self.app.add_api_route("/", self.root, methods=["GET"], response_class=HTMLResponse)
        self.app.add_api_route("/learn", self.learn, methods=["GET"], response_class=HTMLResponse)
        self.app.add_api_route("/pricing", self.pricing, methods=["GET"], response_class=HTMLResponse)
        self.app.add_api_route("/contacts", self.contacts, methods=["GET"], response_class=HTMLResponse)
        self.app.add_api_route("/registration", self.registration, methods=["GET"], response_class=HTMLResponse)
        self.app.add_api_route("/settings", self.settings_me, methods=["GET"], response_class=HTMLResponse)
        self.app.add_api_route("/settings/{userid}", self.settings, methods=["GET"], response_class=HTMLResponse)
        self.app.add_api_route("/vocabulary", self.vocabulary_page, methods=["GET"], response_class=HTMLResponse)
        self.app.add_api_route("/technical-support", self.technical_support, methods=["GET"], response_class=HTMLResponse)
        self.app.add_api_route("/api/technical-support/certificates", self.api_get_user_certificates, methods=["POST"])
        self.app.add_api_route("/api/technical-support/all-pending", self.api_get_all_pending_certificates, methods=["GET"])
        self.app.add_api_route("/api/technical-support/assess", self.api_assess_certificate, methods=["POST"])
        self.app.add_api_route("/api/register", self.register_user, methods=["POST"])
        self.app.add_api_route("/login", self.login, methods=["GET"], response_class=HTMLResponse)
        self.app.add_api_route("/api/login", self.api_login, methods=["POST"])
        self.app.add_api_route("/api/session", self.session_info, methods=["GET"])
        self.app.add_api_route("/api/vocabulary", self.api_get_vocabulary, methods=["GET"])
        self.app.add_api_route("/api/vocabulary", self.api_add_word, methods=["POST"])
        self.app.add_api_route("/api/vocabulary", self.api_delete_word, methods=["DELETE"])
        self.app.add_api_route("/api/change-password", self.change_password, methods=["POST"])
        self.app.add_api_route("/api/upload-certificate", self.cloud_certificate, methods=["POST"])
        self.app.add_api_route("/api/upload-image", self.upload_image_endpoint, methods=["POST"])
        self.app.add_api_route("/api/update-native-language", self.native_language_changes, methods=["POST"])
        self.app.add_api_route("/api/update-interface-language", self.interface_language_changes, methods=["POST"])
        self.app.add_api_route("/api/update-email", self.email_changes, methods=["POST"])
        self.app.add_api_route("/api/generate-exam", self.generate_exam, methods=["GET"])
        self.app.add_api_route("/api/submit-exam", self.submit_exam, methods=["POST"])
        self.app.add_api_route("/api/generate-course", self.generate_course, methods=["POST"])
        self.app.add_api_route("/api/submit_module_answers", self.submit_module_answers, methods=["POST"])
        self.app.add_api_route("/api/get_courses", self.get_courses, methods=["GET"])
        self.app.add_api_route("/api/generate-module", self.generate_module, methods=["GET"])
        self.app.add_api_route("/learn/course{course_id}", self.learn_course, methods=["GET"])
        self.app.add_api_route("/learn/course{course_id}/module{module_number}", self.learn_course_module, methods=["GET"])
        self.app.add_api_route("/api/get-modules", self.api_get_modules, methods=["POST"])
        self.app.add_api_route("/api/submit-module-feedback", self.submit_module_feedback, methods=["POST"])
        self.app.add_api_route("/api/submit-module-progress", self.submit_module_progress, methods=["POST"])

    def _ensure_authenticated(self, request: Request):
        user_id = request.session.get("user_id")
        if not user_id:
            raise HTTPException(status_code=401, detail="Not authenticated.")
        return user_id

    async def _extract_payload_value(self, request: Request, key: str):
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

    async def root(self, request: Request):
        return self.templates.TemplateResponse(request, "index.html")

    async def learn(self, request: Request, exam: str = None):
        level = request.session.get("proficiency_level")
        user_id = request.session.get("user_id")
        role = request.session.get("user_role")

        if role == "Technical Support":
            return self.templates.TemplateResponse(request, "technical_support.html", {"request": request})

        if not level and user_id:
            user = self.db.get_user_by_id(user_id)
            if user and user.get("proficiency_level"):
                 level = user["proficiency_level"]
                 request.session["proficiency_level"] = level

        if level:
            return self.templates.TemplateResponse(request, "learning_dashboard.html", {"request": request, "level": level})
        if exam and exam != "current":
            try:
                test_id = int(exam)
                test_data = self.db.get_test(test_id)
                if test_data and test_data["test_html"]:
                     return self.templates.TemplateResponse(request, "level_confirmation.html", {
                        "request": request, 
                        "exam_content": test_data["test_html"],
                        "test_id": test_id
                    })
            except ValueError:
                pass

        if exam == "current" and "exam_content" in request.session:
            return self.templates.TemplateResponse(request, "level_confirmation.html", {
                "request": request, 
                "exam_content": request.session["exam_content"],
                "test_id": "session" 
            })

        if not level:
            return self.templates.TemplateResponse(request, "level_confirmation.html", {"request": request})
        else:
            return self.templates.TemplateResponse(request, "learning_dashboard.html", {"request": request, "level": level})

    async def pricing(self, request: Request):
        return self.templates.TemplateResponse(request, "pricing.html")

    async def contacts(self, request: Request):
        return self.templates.TemplateResponse(request, "contacts.html")

    async def technical_support(self, request: Request):
        user_id = request.session.get("user_id")
        if not user_id:
            return RedirectResponse(url="/login", status_code=302)

        role = request.session.get("user_role")
        if not role:
            user = self.db.get_user_by_id(user_id)
            role = user.get("role") if user else None
            if role:
                request.session["user_role"] = role

        if role != "Technical Support":
            return RedirectResponse(url="/learn", status_code=302)

        return self.templates.TemplateResponse(request, "technical_support.html", {"request": request})

    async def registration(self, request: Request):
        user_id = request.session.get("user_id")
        if user_id:
            return RedirectResponse(url=f"/settings/{user_id}", status_code=302)
        return self.templates.TemplateResponse(request, "registration.html")

    async def settings_me(self, request: Request):
        user_id = request.session.get("user_id")
        if not user_id:
            return RedirectResponse(url="/login", status_code=302)
        user = self.db.get_user_by_id(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        return self.templates.TemplateResponse(request, "settings.html", {"userid": user_id, "user": user})

    async def settings(self, request: Request, userid: int):
        user_id = request.session.get("user_id")
        if not user_id:
            return RedirectResponse(url="/login", status_code=302)
        if user_id != userid:
            return RedirectResponse(url=f"/settings/{user_id}", status_code=302)
        user = self.db.get_user_by_id(userid)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        return self.templates.TemplateResponse(request, "settings.html", {"userid": userid, "user": user})

    async def vocabulary_page(self, request: Request):
        user_id = request.session.get("user_id")
        if not user_id:
            return RedirectResponse(url="/login", status_code=302)

        user = self.db.get_user_by_id(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        return self.templates.TemplateResponse(request, "vocabulary.html", {"user": user})

    async def technical_support(self, request: Request):
        user_id = request.session.get("user_id")
        if not user_id:
            return RedirectResponse(url="/login", status_code=302)

        role = request.session.get("user_role")
        if not role:
            user = self.db.get_user_by_id(user_id)
            role = user.get("role") if user else None
            if role:
                request.session["user_role"] = role

        if role != "Technical Support":
            return RedirectResponse(url="/learn", status_code=302)

        return self.templates.TemplateResponse(request, "technical_support.html", {"request": request})

    async def api_get_user_certificates(self, request: Request):
        """Get certificates for a user by email or user_id."""
        try:
            data = await request.json()
            email = data.get("email", "").strip()
            user_id = data.get("user_id", "")

            user = None
            if email:
                user_id = self.db.get_user_id_by_email(email)
                if user_id:
                    user = self.db.get_user_by_id(user_id)
            elif user_id:
                try:
                    user_id = int(user_id)
                    user = self.db.get_user_by_id(user_id)
                except (ValueError, TypeError):
                    pass

            if not user:
                return JSONResponse(status_code=404, content={"success": False, "message": "User not found."})

            certificates = self.db.get_certificates_by_user(user["id"])
            return JSONResponse(status_code=200, content={
                "success": True,
                "user": {"id": user["id"], "name": user["name"], "surname": user["surname"], "proficiency_level": user.get("proficiency_level")},
                "certificates": certificates
            })
        except Exception as e:
            return JSONResponse(status_code=400, content={"success": False, "message": str(e)})

    async def api_get_all_pending_certificates(self, request: Request):
        """Get all pending certificates (status = 0) across all users."""
        admin_id = request.session.get("user_id")
        if not admin_id:
            return JSONResponse(status_code=401, content={"success": False, "message": "Not authenticated."})

        try:
            certificates = self.db.get_pending_certificates()
            return JSONResponse(status_code=200, content={
                "success": True,
                "certificates": certificates
            })
        except Exception as e:
            return JSONResponse(status_code=400, content={"success": False, "message": str(e)})

    async def api_assess_certificate(self, request: Request):
        """Assess a pending certificate and update user level."""
        admin_id = request.session.get("user_id")
        if not admin_id:
            return JSONResponse(status_code=401, content={"success": False, "message": "Not authenticated."})

        try:
            data = await request.json()
            certificate_id = data.get("certificate_id")
            user_id = data.get("user_id")
            level = data.get("level", "").upper()
            note = data.get("note", "").strip()

            if not all([certificate_id, user_id, level]):
                return JSONResponse(status_code=400, content={"success": False, "message": "Missing required fields."})

            valid_levels = ["A0", "A1", "A2", "B1", "B2", "C1", "C2"]
            if level not in valid_levels:
                return JSONResponse(status_code=400, content={"success": False, "message": f"Invalid level. Must be one of: {', '.join(valid_levels)}"})

            success, message = self.db.assess_certificate(certificate_id, user_id, level, note)
            return JSONResponse(status_code=200, content={"success": success, "message": message})
        except Exception as e:
            return JSONResponse(status_code=400, content={"success": False, "message": str(e)})

    async def register_user(
        self,
        name: str = Form(...),
        surname: str = Form(...),
        email: str = Form(...),
        password: str = Form(...)
    ):
        success, message = self.db.create_user(name, surname, email, password)
        
        if success:
            return JSONResponse(status_code=200, content={"success": True, "message": message})
        else:
            return JSONResponse(status_code=400, content={"success": False, "message": message})

    async def login(self, request: Request):
        user_id = request.session.get("user_id")
        if user_id:
            return RedirectResponse(url=f"/settings/{user_id}", status_code=302)
        return self.templates.TemplateResponse(request, "login.html")

    async def api_login(
        self,
        request: Request,
        email: str = Form(...),
        password: str = Form(...)
    ):
        success, user_data = self.db.login_user(email, password)


        if not success:
            return JSONResponse(status_code=401, content={"success": False, "message": user_data})

        request.session["user_email"] = user_data["email"]
        request.session["user_id"] = user_data["id"]
        request.session["user_role"] = user_data.get("role")

        full_user = self.db.get_user_by_id(user_data["id"])
        if full_user:
            request.session["proficiency_level"] = full_user.get("proficiency_level")
            if not request.session.get("user_role"):
                request.session["user_role"] = full_user.get("role")

        return RedirectResponse(url=f"/settings/{user_data['id']}", status_code=302)

    async def session_info(self, request: Request):
        return {
            "user_id": request.session.get("user_id"),
            "user_email": request.session.get("user_email"),
            "user_role": request.session.get("user_role"),
        }

    async def api_get_vocabulary(self, request: Request):
        try:
            user_id = self._ensure_authenticated(request)
        except HTTPException as exc:
            return JSONResponse(status_code=exc.status_code, content={"success": False, "message": exc.detail})

        words = self.db.get_vocabulary_by_user(user_id)
        return JSONResponse(status_code=200, content={"success": True, "words": words})

    async def api_add_word(self, request: Request):
        try:
            user_id = self._ensure_authenticated(request)
        except HTTPException as exc:
            return JSONResponse(status_code=exc.status_code, content={"success": False, "message": exc.detail})

        payload = await request.json()
        word = payload.get("word", "").strip()
        definition = payload.get("definition", "").strip()

        if not word or not definition:
            return JSONResponse(status_code=400, content={"success": False, "message": "Word and definition are required."})

        words = self.db.get_vocabulary_by_user(user_id)
        words[word] = definition
        self.db.save_vocabulary_by_user(user_id, words)

        return JSONResponse(status_code=200, content={"success": True, "words": words, "message": "Word saved."})

    async def api_delete_word(self, request: Request):
        try:
            user_id = self._ensure_authenticated(request)
        except HTTPException as exc:
            return JSONResponse(status_code=exc.status_code, content={"success": False, "message": exc.detail})

        payload = await request.json()
        word = payload.get("word", "").strip()

        if not word:
            return JSONResponse(status_code=400, content={"success": False, "message": "Word is required."})

        words = self.db.get_vocabulary_by_user(user_id)

        if word not in words:
            return JSONResponse(status_code=404, content={"success": False, "message": "Word not found."})

        del words[word]
        self.db.save_vocabulary_by_user(user_id, words)

        return JSONResponse(status_code=200, content={"success": True, "words": words, "message": "Word deleted."})

    async def change_password(self, request: Request,
        old_password: str = Form(...),
        new_password: str = Form(...)
    ):
        user_id = request.session.get("user_id")
        if not user_id:
            return JSONResponse(status_code=401, content={"success": False, "message": "Not authenticated."})

        user = self.db.get_user_by_id(user_id)
        if not user:
            return JSONResponse(status_code=404, content={"success": False, "message": "User not found."})

        stored_hash = user['password_hash']
        if not PasswordHash.recommended().verify(old_password, stored_hash):
            return JSONResponse(status_code=400, content={"success": False, "message": "Incorrect old password."})

        self.db.rechange_password(user_id, new_password)

        return JSONResponse(status_code=200, content={"success": True, "message": "Password changed successfully."})

    async def cloud_certificate(self, request: Request, file: UploadFile = File(...)):
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
        self.db.upload_certificate(user_id, rel_path)

        static_url = f"/static/{rel_path}"
        return JSONResponse(status_code=200, content={"success": True, "path": rel_path, "url": static_url, "message": "Certificate uploaded successfully."})

    async def upload_image_endpoint(self, request: Request, file: UploadFile = File(...)):
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
        self.db.upload_image(user_id, rel_path)

        static_url = f"/static/profile_images/{safe_name}"
        return JSONResponse(status_code=200, content={"success": True, "path": rel_path, "url": static_url, "message": "Profile image uploaded successfully."})

    async def native_language_changes(self, request: Request):
        user_id = request.session.get("user_id")
        if not user_id:
            return JSONResponse(status_code=401, content={"success": False, "message": "Not authenticated."})

        native_language = await self._extract_payload_value(request, "native_language")
        if not native_language:
            native_language = await self._extract_payload_value(request, "native-language")

        if not native_language:
            return JSONResponse(status_code=400, content={"success": False, "message": "Native language is required."})

        self.db.update_native_language(user_id, native_language)

        return JSONResponse(status_code=200, content={"success": True, "message": "Native language updated successfully."})

    async def interface_language_changes(self, request: Request):
        user_id = request.session.get("user_id")
        if not user_id:
            return JSONResponse(status_code=401, content={"success": False, "message": "Not authenticated."})

        interface_language = await self._extract_payload_value(request, "interface_language")
        if not interface_language:
            interface_language = await self._extract_payload_value(request, "interface-language")

        if not interface_language:
            return JSONResponse(status_code=400, content={"success": False, "message": "Interface language is required."})

        self.db.update_interface_language(user_id, interface_language)

        return JSONResponse(status_code=200, content={"success": True, "message": "Interface language updated successfully."})

    async def email_changes(self, request: Request):
        user_id = request.session.get("user_id")
        if not user_id:
            return JSONResponse(status_code=401, content={"success": False, "message": "Not authenticated."})

        email = await self._extract_payload_value(request, "email")

        if not email:
            return JSONResponse(status_code=400, content={"success": False, "message": "Email is required."})

        self.db.update_email(user_id, email)

        return JSONResponse(status_code=200, content={"success": True, "message": "Email updated successfully."})

    async def generate_exam(self, request: Request):
        user_id = request.session.get("user_id")
        if not user_id:
            return JSONResponse(status_code=401, content={"success": False, "message": "Not authenticated."})

        try:
            generation_result = self.phoenix_tracker.generate(
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
            test_id = self.db.create_pending_test(user_id, generation_result["content"])
            return JSONResponse(status_code=200, content={"success": True, "exam": {"id": test_id}})
        except Exception as e:
            print(f"Error generating exam: {e}")
            return JSONResponse(status_code=500, content={"success": False, "message": str(e)})

    async def submit_exam(self, request: Request):
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
                test_data = self.db.get_test(int(test_id_val))
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
        feedback_result = self.phoenix_tracker.generate(
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
                self.db.update_test_submission(
                    test_id=int(test_id_val),
                    submitted_answers_json=exam_answers,
                    assessed_level=feedback,
                    assessed_by_model="gemini-2.5-flash-preview-09-2025",
                    phoenix_run_id=run_id
                )
            except Exception as e:
                print(f"Error updating test: {e}")
        else:
            self.db.add_test(
                user_id=user_id,
                test_html=request.session.get("exam_content", ""),
                submitted_answers_json=exam_answers,
                assessed=True,
                assessed_level=feedback,
                assessed_by_model="gemini-2.5-flash-preview-09-2025",
                phoenix_run_id=run_id
            )
        self.db.update_english_level(user_id, feedback)
        return JSONResponse(status_code=200, content={"success": True, "feedback": feedback})

    async def generate_course(self, request: Request, level: str):
        user_id = request.session.get("user_id")
        if not user_id:
            return JSONResponse(status_code=401, content={"success": False, "message": "Not authenticated."})
        response = self.phoenix_tracker.generate(
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

        course_id = self.db.add_course(level=level, title=course_content.get('title'), description=course_content.get('description'), 
                      duration_weeks=course_content.get('duration_weeks'), course_plan=str(course_content.get('course_plan')))

        start_date = time.strftime("%Y-%m-%d")
        self.db.enroll_user_in_course(user_id=user_id, course_id=course_id, start_date=start_date)

        return JSONResponse(status_code=200, content={"success": True, "course": course_content})

    async def submit_module_answers(self, request: Request):
        user_id = request.session.get("user_id")
        if not user_id:
            return JSONResponse(status_code=401, content={"success": False, "message": "Not authenticated."})
        
        data = await request.json()
        submission_url = data.get("url", "")
        exercises = data.get("exercises", [])

        course_id_match = re.search(r'course(\d+)', submission_url)
        module_num_match = re.search(r'module(\d+)', submission_url)
        
        course_id = course_id_match.group(1) if course_id_match else "unknown"
        module_number = module_num_match.group(1) if module_num_match else "unknown"

        exercises_text = ""
        for ex in exercises:
            exercises_text += f"Exercise {ex.get('id')}:\nContext: {ex.get('question_context')}\nUser Answer: {ex.get('user_answer')}\n\n"

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

        response = self.phoenix_tracker.generate(
            temperature=0.3,
            model="gemini-2.5-flash-preview-09-2025",
            prompt_context=prompt,
            name="Module Grading",
            type="grading", 
            collection_name="CefrGrammarProfile"
        )

        feedback_html = response["content"] 
        
        if isinstance(feedback_html, str) and feedback_html.strip().startswith("```html"):
             feedback_html = feedback_html.strip().split("\n", 1)[1].rsplit("\n", 1)[0]
        
        return JSONResponse(status_code=200, content={"success": True, "feedback_html": feedback_html})

    async def get_courses(self, request: Request):
        user_id = request.session.get("user_id")
        if not user_id:
            return JSONResponse(status_code=401, content={"success": False, "message": "Not authenticated."})
        courses = self.db.get_user_courses(user_id)
        return JSONResponse(status_code=200, content={"success": True, "courses": courses})

    async def generate_module(self, request: Request, course_id: int, module_number: int):
        user_id = request.session.get("user_id")
        if not user_id:
            return JSONResponse(status_code=401, content={"success": False, "message": "Not authenticated."})
        content = self.db.get_module_content(module_number, course_id)
        if content:
            return JSONResponse(status_code=200, content={"success": True, "module": content})
        course = self.db.get_course_by_id(course_id)
        course_plan = course.get("course_plan", "")
        response = self.phoenix_tracker.generate(
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
            
        self.db.add_module(course_id=course_id, title=f"Module {module_number}", week_number=module_number, content_html=str(module_content), phoenix_id=phoenix_run_id)
        return JSONResponse(status_code=200, content={"success": True, "module": module_content})

    async def learn_course(self, request: Request, course_id: int):
        user_id = request.session.get("user_id")
        if not user_id:
            return RedirectResponse(url="/login", status_code=302)

        course = self.db.get_course_by_id(course_id)
        if not course:
            raise HTTPException(status_code=404, detail="Course not found")

        modules = self.db.get_modules_by_course(course_id)

        return self.templates.TemplateResponse(request, "course_learning.html", {
            "request": request,
            "course": course,
            "modules": modules
        })

    async def learn_course_module(self, request: Request, course_id: int, module_number: int):
        user_id = request.session.get("user_id")
        if not user_id:
            return RedirectResponse(url="/login", status_code=302)

        course = self.db.get_course_by_id(course_id)
        if not course:
            raise HTTPException(status_code=404, detail="Course not found")
        
        modules = self.db.get_modules_by_course(course_id)
        current_module = next((m for m in modules if m["week_number"] == module_number), None)
        
        if not current_module:
             pass

        if current_module and current_module.get("content_html"):
            try:
                import ast
                content_data = None
                raw_content = current_module["content_html"]
                
                try:
                    cleaned_raw = raw_content
                    if '" + "' in cleaned_raw or "' + '" in cleaned_raw:
                        cleaned_raw = re.sub(r'"\s*\+\s*"', "", cleaned_raw)
                        cleaned_raw = re.sub(r"'\s*\+\s*'", "", cleaned_raw)
                        
                    content_data = json.loads(cleaned_raw)
                except:
                    try:
                        cleaned = raw_content.strip()
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
                     current_module["rendered_html"] = raw_content

            except Exception as e:
                print(f"Error preparing module content: {e}")
                current_module["rendered_html"] = "Error loading content."

        return self.templates.TemplateResponse(request, "course_module.html", {
            "request": request,
            "course": course,
            "module": current_module,
            "module_number": module_number
        })

    async def api_get_modules(self, request: Request, course_id: int):
        user_id = request.session.get("user_id")
        if not user_id:
            return JSONResponse(status_code=401, content={"success": False, "message": "Not authenticated."})
            
        db_modules = self.db.get_modules_by_course(course_id)
        created_map = {m['week_number']: m for m in db_modules}
        
        final_modules = []
        
        course = self.db.get_course_by_id(course_id)
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

    async def submit_module_feedback(self, request: Request):
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
            self.db.assess_module_user(
                user_id=user_id,
                module_id=annotations.get("module_id"),
                course_id=annotations.get("course_id"),
                rating=annotations.get("score"),
                review=annotations.get("review"),
            )
            print(f"Feedback stored in database for user {user_id}, module {annotations.get('module_id')}")
            
            if span_id and span_id != "None" and span_id.strip():
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
                        print(f"Annotation added to Phoenix successfully via REST API")
                    else:
                        print(f"WARNING: Phoenix annotation failed with status {response.status_code}: {response.text}")

                except Exception as e:
                    print(f"WARNING: Phoenix annotation failed (feedback still saved): {type(e).__name__}: {str(e)}")
            else:
                print(f"WARNING: No valid span_id provided. Feedback saved but not annotated in Phoenix.")
            
            return JSONResponse(status_code=200, content={"success": True, "message": "Feedback submitted and saved."})
        except Exception as e:
            print(f"ERROR: Failed to save feedback: {type(e).__name__}: {str(e)}")
            import traceback
            traceback.print_exc()
            return JSONResponse(status_code=500, content={"success": False, "message": f"Error saving feedback: {str(e)}"})

    async def submit_module_progress(self, request: Request):
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

        module_content_html = self.db.get_module_content(module_id, course_id)
        
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
            generation_result = self.phoenix_tracker.generate(
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
                
            self.db.add_progress_tracking(
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

fluent_app = FluentMindApp()
app = fluent_app.app
