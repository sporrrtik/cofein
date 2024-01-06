import os
from contextlib import suppress

from flask import Flask
from flask_admin import Admin

from database import SessionLocal
from models import Item, Order



def init_flask() -> Flask:
    app = Flask('auction_admin')
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'devsecretkey1111')
    app.config['FLASK_ADMIN_FLUID_LAYOUT'] = True

    def sqla_session_middleware(environ, start_response):
        with SessionLocal.begin():
            return wsgi_app(environ, start_response)

    wsgi_app = app.wsgi_app
    app.wsgi_app = sqla_session_middleware

    return app


app = init_flask()
admin = Admin(app, name='Coffee Shop Admin', template_mode='bootstrap4')


from flask_admin.contrib.sqla import ModelView


class SQLAModelView(ModelView):
    is_id: bool = True
    column_display_pk = True

    model: type[ModelView]
    page_size = 40

    def __init__(self, model: type[ModelView] = None, **kwargs):
        super().__init__(model or self.model, SessionLocal(), **kwargs)


class ItemsView(SQLAModelView):
    model = Item

    column_filters = (
        'id',
        'title',
        'description',
        'price',
    )


class OrdersView(SQLAModelView):
    model = Order

    column_filters = (
        'id',
        'email',
        'ordered_items',
        'total_price',
        'active',
    )


with SessionLocal.begin():
    admin.add_views(
        ItemsView(name='Меню'),
        OrdersView(name='Заказы'),
    )


# XXX: Remove "Home" page
admin.menu().pop(0)

app.run('0.0.0.0', 8001)