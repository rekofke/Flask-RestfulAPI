from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from flask_marshmallow import Marshmallow
from datetime import date
from typing import List
from marshmallow import ValidationError, fields
from sqlalchemy import select, delete


# Initialize Flask app
app = Flask(__name__)

# configure MYSQL DB
app.config('SQLALCHEMY_DATABASE_URI') = 'mysql+myswlconnector://root:C%40ntget1n@localhost/flask_api_db'
# app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Create base model
class Base(DeclarativeBase):
    pass

# Initialize SQLAlchemy and Marshmallow
db = SQLAlchemy(model_class=Base)
db.init_app(app)
ma = Marshmallow(app)

#========== MODELS ==========

class Customer(Base):

   __tablename__ = 'Customer'

   id: Mapped[int] = mapped_column(primary_key=True)
   name: Mapped[str] = mapped_column(db.String(225), nullable=False)
   email: Mapped[str] = mapped_column(db.String(225))
   address: Mapped[str] = mapped_column(db.String(225))

   # one-to-many relationship with Orders
   orders: Mapped[List["Orders"]] = db.relationship(back_populates='Customer') # ensures access from both ends of relationship

# Association Table - facilitates one order to many products, or many products to one order (many-to-many)
order_products = db.Table(
    "Order_Products",
    Base.metadata,  # allows table to locate the foreign keys from the other tables
    db.Column('order_id', db.ForeignKey('orders.id')),
    db.Column('product_id', db.ForeignKey('products.id'))
)



class Orders(Base):
   __tablename__ = 'Orders' 

   id: Mapped[int] = mapped_column(primary_key=True)
   order_date: Mapped[date] = mapped_column(db.Date, nullable=False)
   customer_id: Mapped['Customer'] = db.ForeignKey('Customer.id')
   # many-to-one relationship with Customer
   customer: Mapped['Customer'] = db.relationship(back_populates='Orders')
   # many-to-many relationship with Products
   products: Mapped[List['Products']] = db.relationship(secondary=order_products, back_populates="Orders")
 


class Products(Base):
    __tablename__ = 'Products'

    id: Mapped[int] = mapped_column(primary_key=True)
    product_name: Mapped[str] = mapped_column(db.String(225), nullable=False)
    price: Mapped[float]  = mapped_column(db.Float, nullable=False)
    orders: Mapped[List['Orders']] = db.relationship(secondary=order_products, back_populates="Products")

# initialize DB and create tables
with app.app_context():
    # db.drop_all()

    db.create_all()

#========== SCHEMAS ==========

# Customer Schema
class CustomerSchema(ma.SQLAlchemyAutoSchema): # create schema fields based on SQLAlchemy model
    class Meta:
        model = Customer

class ProductSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Products

class OrderSchema(ma.SQLAlchenyAutoSchema):
    class Meta
    model = Orders
    include_fk = True # to assist Auto Schema in recognizing foreign keys

customer_schema = CustomerSchema()
customers_schema = CustomerSchema(many=True)

product_schema = ProductSchema()
products_schema = ProductSchema(many=True)

order_schema = OrderSchema()
orders_schema = OrderSchema(many=True)

