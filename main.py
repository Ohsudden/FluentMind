from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from starlette.staticfiles import StaticFiles
import uvicorn
from database import init_db, create_user

app = FastAPI()

@app.on_event("startup")
async def startup_event():
    init_db()

app.mount("/static", StaticFiles(directory="static"), name="static")

templates = Jinja2Templates(directory="static")

@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/pricing", response_class=HTMLResponse)
async def pricing(request: Request):
    return templates.TemplateResponse("pricing.html", {"request": request})

@app.get("/contacts", response_class=HTMLResponse)
async def contacts(request: Request):
    return templates.TemplateResponse("contacts.html", {"request": request})

@app.get("/registration", response_class=HTMLResponse)
async def registration(request: Request):
    return templates.TemplateResponse("registration.html", {"request": request})

@app.post("/api/register")
async def register_user(
    name: str = Form(...),
    surname: str = Form(...),
    email: str = Form(...),
    password: str = Form(...)
):
    success, message = create_user(name, surname, email, password)
    
    if success:
        return JSONResponse(
            status_code=200,
            content={"success": True, "message": message}
        )
    else:
        return JSONResponse(
            status_code=400,
            content={"success": False, "message": message}
        )
