from fastapi import FastAPI, Request, Form, HTTPException, UploadFile, File
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from starlette.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware
from database import init_db, create_user, login_user, get_user_by_id, rechange_password, upload_certificate, upload_image
from pwdlib import PasswordHash
import os, time, secrets


init_db()
app = FastAPI()

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
    session_user_id = request.session.get("user_id")
    if not session_user_id:
        return RedirectResponse(url="/login", status_code=302)
    if session_user_id != userid:
        return RedirectResponse(url=f"/settings/{session_user_id}", status_code=302)
    user = get_user_by_id(userid)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return templates.TemplateResponse("settings.html", {"request": request, "userid": userid, "user": user})

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