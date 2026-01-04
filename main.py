from fastapi import FastAPI, Request, Form, HTTPException, UploadFile, File
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from starlette.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware
from phoenix_tracking import PhoenixTracking
from database import (
    init_db,
    create_user,
    login_user,
    get_user_by_id,
    rechange_password,
    upload_certificate,
    upload_image,
    get_vocabulary_by_user,
    save_vocabulary_by_user,
    update_native_language,
    update_interface_language,
    update_email
)
from pwdlib import PasswordHash
import os, time, secrets


init_db()
app = FastAPI()

phoenix_tracker = PhoenixTracking(app_name="FluentMind")

app.add_middleware(SessionMiddleware, secret_key="dev-secret")

app.mount("/static", StaticFiles(directory="static"), name="static")

templates = Jinja2Templates(directory="static")

@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/learn", response_class=HTMLResponse)
async def learn(request: Request):
    level = request.session.get("proficiency_level")
    if not level:
        return templates.TemplateResponse("level_confirmation.html", {"request": request})
    else:
        return 'Good Job! Your level is already set.' # change this to a proper response later


@app.get("/pricing", response_class=HTMLResponse)
async def pricing(request: Request):
    return templates.TemplateResponse("pricing.html", {"request": request})

@app.get("/contacts", response_class=HTMLResponse)
async def contacts(request: Request):
    return templates.TemplateResponse("contacts.html", {"request": request})

@app.get("/registration", response_class=HTMLResponse)
async def registration(request: Request):
    user_id = request.session.get("user_id")
    if user_id:
        return RedirectResponse(url=f"/settings/{user_id}", status_code=302)
    return templates.TemplateResponse("registration.html", {"request": request})

@app.get("/settings", response_class=HTMLResponse)
async def settings_me(request: Request):
    user_id = request.session.get("user_id")
    if not user_id:
        return RedirectResponse(url="/login", status_code=302)
    user = get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return templates.TemplateResponse("settings.html", {"request": request, "userid": user_id, "user": user})

@app.get("/settings/{userid}", response_class=HTMLResponse)
async def settings(request: Request, userid: int):
    user_id = request.session.get("user_id")
    if not user_id:
        return RedirectResponse(url="/login", status_code=302)
    if user_id != userid:
        return RedirectResponse(url=f"/settings/{user_id}", status_code=302)
    user = get_user_by_id(userid)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return templates.TemplateResponse("settings.html", {"request": request, "userid": userid, "user": user})


@app.get("/vocabulary", response_class=HTMLResponse)
async def vocabulary_page(request: Request):
    user_id = request.session.get("user_id")
    if not user_id:
        return RedirectResponse(url="/login", status_code=302)

    user = get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return templates.TemplateResponse("vocabulary.html", {"request": request, "user": user})

@app.post("/api/register")
async def register_user(
    name: str = Form(...),
    surname: str = Form(...),
    email: str = Form(...),
    password: str = Form(...)
):
    success, message = create_user(name, surname, email, password)
    
    if success:
        return JSONResponse(status_code=200, content={"success": True, "message": message})
    else:
        return JSONResponse(status_code=400, content={"success": False, "message": message})

@app.get("/login", response_class=HTMLResponse)
async def login(request: Request):
    user_id = request.session.get("user_id")
    if user_id:
        return RedirectResponse(url=f"/settings/{user_id}", status_code=302)
    return templates.TemplateResponse("login.html", {"request": request})

@app.post("/api/login")
async def api_login(
    request: Request,
    email: str = Form(...),
    password: str = Form(...)
):
    success, user_data = login_user(email, password)

    if not success:
        return JSONResponse(status_code=401, content={"success": False, "message": user_data})

    request.session["user_email"] = user_data["email"]
    request.session["user_id"] = user_data["id"]
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

    words = get_vocabulary_by_user(user_id)
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

    words = get_vocabulary_by_user(user_id)
    words[word] = definition
    save_vocabulary_by_user(user_id, words)

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

    words = get_vocabulary_by_user(user_id)

    if word not in words:
        return JSONResponse(status_code=404, content={"success": False, "message": "Word not found."})

    del words[word]
    save_vocabulary_by_user(user_id, words)

    return JSONResponse(status_code=200, content={"success": True, "words": words, "message": "Word deleted."})

@app.post("/api/change-password")
async def change_password(request: Request,
    old_password: str = Form(...),
    new_password: str = Form(...)
):
    user_id = request.session.get("user_id")
    if not user_id:
        return JSONResponse(status_code=401, content={"success": False, "message": "Not authenticated."})

    user = get_user_by_id(user_id)
    if not user:
        return JSONResponse(status_code=404, content={"success": False, "message": "User not found."})

    stored_hash = user['password_hash']
    if not PasswordHash.recommended().verify(old_password, stored_hash):
        return JSONResponse(status_code=400, content={"success": False, "message": "Incorrect old password."})

    rechange_password(user_id, new_password)

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
    upload_certificate(user_id, rel_path)

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
    upload_image(user_id, rel_path)

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

    update_native_language(user_id, native_language)

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

    update_interface_language(user_id, interface_language)

    return JSONResponse(status_code=200, content={"success": True, "message": "Interface language updated successfully."})

@app.post("/api/update-email")
async def email_changes(request: Request):
    user_id = request.session.get("user_id")
    if not user_id:
        return JSONResponse(status_code=401, content={"success": False, "message": "Not authenticated."})

    email = await _extract_payload_value(request, "email")

    if not email:
        return JSONResponse(status_code=400, content={"success": False, "message": "Email is required."})

    update_email(user_id, email)

    return JSONResponse(status_code=200, content={"success": True, "message": "Email updated successfully."})

@app.get("/api/generate-exam")
async def generate_exam(request: Request):
    user_id = request.session.get("user_id")
    if not user_id:
        return JSONResponse(status_code=401, content={"success": False, "message": "Not authenticated."})

    exam = phoenix_tracker.generate(
        temperature=0.7,
        top_p=0.9,
        max_tokens=2000,
        model="gemini-2.5-pro",
        prompt_context="You are an expert English exam creator. Generate a 5-question multiple-choice "
    )

    return JSONResponse(status_code=200, content={"success": True, "exam": exam})
@app.post("/api/submit-exam")
async def submit_exam(request: Request):
    user_id = request.session.get("user_id")
    if not user_id:
        return JSONResponse(status_code=401, content={"success": False, "message": "Not authenticated."})

    payload = await request.json()
    exam_answers = payload.get("exam_answers", "")

    if not exam_answers:
        return JSONResponse(status_code=400, content={"success": False, "message": "Exam answers are required."})

    feedback = phoenix_tracker.generate(
        exam_answers,
        temperature=0.7,
        top_p=0.9,
        max_tokens=2000,
        model="gemini-2.5-pro",
        context_prompt="You are an expert English tutor. Provide detailed feedback on the submitted exam answers."
    )

    return JSONResponse(status_code=200, content={"success": True, "feedback": feedback})