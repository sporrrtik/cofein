from typing import Annotated
from fastapi import Cookie, Depends, FastAPI, HTTPException, Form, Header, Query
from sqlalchemy import text
from sqlalchemy.orm import Session
from fastapi.templating import Jinja2Templates
from fastapi.requests import Request
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware import Middleware
from starlette import status

import crud, models, schemas
from database import SessionLocal, engine

templates = Jinja2Templates(directory="templates")

models.Base.metadata.create_all(bind=engine)

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")

# Dependency
def get_db() -> Session:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.get("/")
def start(request: Request, db: Session = Depends(get_db)):
    items = crud.get_items(db, limit=6)
    return templates.TemplateResponse("index.html", context={"request": request, 'items': items})


@app.post("/enter")
def enter(email=Form(), password=Form(), db: Session = Depends(get_db)):
    cur_user = crud.get_user_by_email(db, email=email)
    if not cur_user:
        return RedirectResponse("/enter_page")
    rr = RedirectResponse('/lc', status_code=status.HTTP_302_FOUND)
    rr.set_cookie('email', cur_user.email)
    return rr


@app.get("/enter_page")
@app.post("/enter_page")
def enter_page(request: Request, email: Annotated[str | None, Cookie()] = None):
    if email is not None:
        return RedirectResponse('/lc', status_code=status.HTTP_302_FOUND)
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
def personal_page(
    request: Request, 
    email: Annotated[str | None, Cookie()] = None,
    db: Session = Depends(get_db),
):
    if email is None:
        return RedirectResponse('/', status_code=status.HTTP_302_FOUND)
    query = "SELECT c.id, it.id AS itemid, it.title, it.price, it.image_url FROM carts AS c JOIN items AS it ON c.item_id=it.id WHERE email=:email;"
    current_cart = db.execute(text(query).bindparams(email=email)).mappings().all()
    price = 0
    item_ids = []
    for item in current_cart:
        price += item.price
        item_ids.append(item.itemid)
    item_ids = ','.join((str(v) for v in item_ids))

    query = "SELECT * FROM orders WHERE email=:email"
    orders = db.execute(text(query).bindparams(email=email)).mappings().all()
    return templates.TemplateResponse(
        "lc.html",
        context={"request": request, 'orders': orders, 'email': email, 'cart': current_cart, 'price': price, 'item_ids': item_ids},
    )


@app.get('/add_to_cart')
def add_item_to_cart(
    item_id: int | None = Query(default=None),
    email: Annotated[str | None, Cookie()] = None,
    db: Session = Depends(get_db),
):
    if not email:
        return RedirectResponse('/enter_page', status_code=status.HTTP_302_FOUND)
    if not item_id:
        print('no item id in query')
        return RedirectResponse('/', status_code=status.HTTP_302_FOUND)
    try:
        new_cart_item = models.Cart(
            email=email,
            item_id=item_id,
        )
        db.add(new_cart_item)
        db.commit()
    except Exception as e:
        print(f'failed to save cart as {e}')
    return RedirectResponse('/', status_code=status.HTTP_302_FOUND)


@app.get('/delete_from_cart')
def delete_item_from_cart(
    id: int | None = Query(default=None), 
    db: Session = Depends(get_db),
):
    try:
        query = 'DELETE FROM carts WHERE id=:id;'
        db.execute(text(query).bindparams(id=id))
        db.commit()
    except Exception as e:
        print(f'error while deleting {e}')
    return RedirectResponse('/lc', status_code=status.HTTP_302_FOUND)


@app.get('/confirm_order')
def confirm_order(
    item_ids: str | None = Query(default=None),
    price: int | None = Query(default=None),
    email: Annotated[str | None, Cookie()] = None,
    db: Session = Depends(get_db),
):
    try:
        order = models.Order(
            email=email,
            ordered_items=item_ids,
            total_price=price,
        )
        db.add(order)

        query = 'DELETE FROM carts WHERE email=:email;'
        db.execute(text(query).bindparams(email=email))

        db.commit()
    except Exception as e:
        print(f'error while confirming order {e}')
    return RedirectResponse('/lc', status_code=status.HTTP_302_FOUND)


@app.on_event('startup')
async def fill_database():
    session = SessionLocal()
    if session.execute(text('SELECT * FROM items;')).scalars().all():
        return
    item1 = models.Item(
        id=1,
        title='#1. Chicken Chilis',
        image_url='http://127.0.0.1:8000/static/img/delicious/1.png',
        description='Craft beer elit seitan exercitation photo booth et 8-bit kale chips.',
        price=2000
    )
    item2 = models.Item(
        id=2,
        title='#2. Пельмени',
        image_url='http://127.0.0.1:8000/static/img/delicious/2.png',
        description='ну очень вкусные пельмени много мяса мало теста.',
        price=2000
    )
    item3 = models.Item(
        id=3,
        title='#3. Вафли',
        image_url='http://127.0.0.1:8000/static/img/delicious/3.png',
        description='просто вафли.',
        price=2000
    )
    session.add(item1)
    session.add(item2)
    session.add(item3)
    session.commit()

