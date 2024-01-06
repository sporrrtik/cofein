from fastapi import Depends, FastAPI, HTTPException, Form
from sqlalchemy.orm import Session
from fastapi.templating import Jinja2Templates
from fastapi.requests import Request
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware import Middleware

import crud, models, schemas
from database import SessionLocal, engine

templates = Jinja2Templates(directory="templates")

models.Base.metadata.create_all(bind=engine)

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.get("/")
def start(request: Request):
    return templates.TemplateResponse("index.html", context={"request": request})


@app.post("/enter")
def enter(email=Form(), password=Form(), db: Session = Depends(get_db)):
    cur_user = crud.get_user_by_email(db, email=email)
    if not cur_user:
        return RedirectResponse("/enter_page")
    return cur_user


@app.get("/enter_page")
@app.post("/enter_page")
def enter_page(request: Request):
    return templates.TemplateResponse("enter.html", context={"request": request})


@app.post("/reg")
def registrate(request: Request, db: Session = Depends(get_db), email=Form(), password=Form(), password2=Form()):
    if password == password2:
        db_user = crud.get_user_by_email(db, email=email)
        if db_user:
            return templates.TemplateResponse("registration.html", context={"request": request, "error": "Аккаунт уже существует"})
        return crud.reg_user(db, email, password)
    return templates.TemplateResponse("registration.html", context={"request": request, "error": "Пароли не совпадают"})


@app.get("/registration_page")
def registration_page(request: Request):
    return templates.TemplateResponse("registration.html", context={"request": request})


@app.get("/lc")
def personal_page(request: Request):
    return templates.TemplateResponse("lc.html", context={"request": request})


@app.post("/users/", response_model=schemas.User)
def create_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    db_user = crud.get_user_by_email(db, email=user.email)
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    return crud.create_user(db=db, user=user)


@app.get("/users/", response_model=list[schemas.User])
def read_users(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    users = crud.get_users(db, skip=skip, limit=limit)
    return users


@app.get("/users/{user_id}", response_model=schemas.User)
def read_user(user_id: int, db: Session = Depends(get_db)):
    db_user = crud.get_user(db, user_id=user_id)
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user


@app.post("/users/{user_id}/items/", response_model=schemas.Item)
def create_item_for_user(user_id: int, item: schemas.ItemCreate, db: Session = Depends(get_db)):
    return crud.create_user_item(db=db, item=item, user_id=user_id)


@app.get("/items/", response_model=list[schemas.Item])
def read_items(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    items = crud.get_items(db, skip=skip, limit=limit)
    return items
