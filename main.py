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
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+mysqlconnector://root:C%40ntget1n@localhost/flask_api_db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Create base model
class Base(DeclarativeBase):
    pass

# Initialize SQLAlchemy and Marshmallow
db = SQLAlchemy(model_class=Base)
db.init_app(app)
ma = Marshmallow(app)

#========== MODELS ==========

class Customer(Base):

    __tablename__ = 'customer'

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(db.String(225), nullable=False)
    email: Mapped[str] = mapped_column(db.String(225))
    address: Mapped[str] = mapped_column(db.String(225))

    # one-to-many relationship with Orders
    orders: Mapped[List["Orders"]] = db.relationship(back_populates="customer") # ensures access from both ends of relationship

# Association Table - facilitates one order to many products, or many products to one order (many-to-many)
order_products = db.Table(
    "order_products",
    Base.metadata,
    db.Column('order_id', db.ForeignKey('orders.id')), 
    db.Column('product_id', db.ForeignKey('products.id')) 
)




class Orders(Base):
    __tablename__ = 'orders' 

    id: Mapped[int] = mapped_column(primary_key=True)
    order_date: Mapped[date] = mapped_column(db.Date, nullable=False)
    customer_id: Mapped[int] = mapped_column(db.ForeignKey('customer.id'))
    # many-to-one relationship with Customer
    customer: Mapped['Customer'] = db.relationship(back_populates="orders")
    products: Mapped[List['Products']] = db.relationship(secondary=order_products, back_populates="orders")  




class Products(Base):
    __tablename__ = 'products'

    id: Mapped[int] = mapped_column(primary_key=True)
    product_name: Mapped[str] = mapped_column(db.String(225), nullable=False)
    price: Mapped[float]  = mapped_column(db.Float, nullable=False)
    orders: Mapped[List['Orders']] = db.relationship(secondary=order_products, back_populates="products")

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

class OrderSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Orders
        include_fk = True # to assist Auto Schema in recognizing foreign keys

customer_schema = CustomerSchema()
customers_schema = CustomerSchema(many=True)

product_schema = ProductSchema()
products_schema = ProductSchema(many=True)

order_schema = OrderSchema()
orders_schema = OrderSchema(many=True)

#========== API ROUTES - Flask ==========

@app.route('/')
def home():
    return "Home"


#========== API ROUTES: Customer ==========

# Create new customer (POST)

@app.route("/customers", methods=['POST'])
def add_customer():
    try:
        customer_data = customer_schema.load(request.json)
    except ValidationError as e:
        return jsonify(e.messages), 400
    
    new_customer = Customer(name=customer_data['name'], email=customer_data['email'], address=customer_data['address'])
    db.session.add(new_customer)
    db.session.commit()

    return jsonify({"Message": "New Customer added successfully", 
                    "Customer": customer_schema.dump(new_customer)}), 201

# Get all customers (GET)

@app.route("/customers", methods=["GET"])
def get_customers():
    query = select(Customer) # query customers table and convert row objects into usable python objects with scalars
    result = db.session.execute(query).scalars()
    customers = result.all() # convert to list of customer objects
    return customers_schema.jsonify(customers), 200 # serializes list of customers into JSON format, returns users and status code 200

# Get customer by ID (GET)

@app.route('/customers/<int:id>', methods=["GET"])
def get_customer(id):
    query = select(Customer).where(Customer.id == id)
    customer = db.session.execute(query).scalars().first()

    if customer is None:
        return jsonify({"Error": "Customer not found"}), 404
    
    return customer_schema.jsonify(customer), 200  # serializes customer into JSON format, returns user and status code 200

# Update customer (PUT)

@app.route('/customers/<int:id>', methods=["PUT"])
def update_customer(id):
    customer = db.session.get(Customer, id)  # Variable renamed to 'customer'

    if not customer:
        return jsonify({"Message": "Invalid customer id"}), 400
    
    try:
        customer_data = customer_schema.load(request.json)
    except ValidationError as e:
        return jsonify(e.messages), 400
    
    customer.name = customer_data['name']
    customer.email = customer_data['email']
    customer.address = customer_data['address']

    db.session.commit()
    return customer_schema.jsonify(customer), 200 

# Delete customer (DELETE)

@app.route("/customers/<int:id>", methods=["DELETE"])
def delete_customer(id):
    customer = db.session.get(Customer, id)  # Variable renamed to 'customer'

    if not customer:
        return jsonify({"Message": "Invalid customer id"}), 400
    
    db.session.delete(customer)
    db.session.commit()
    return jsonify({"Message": "Customer deleted successfully"}), 200
 # returns success message and status code 200

#========== API ROUTES: Products ==========
# Create new product (POST)

@app.route("/products", methods=["POST"])
def create_product():
    try:
        product_data = product_schema.load(request.json)
    except ValidationError as e:
        return jsonify(e.messages), 400
    
    new_product = Products(product_name=product_data['product_name'], price=product_data['price'])
    db.session.add(new_product)
    db.session.commit()

    return jsonify({"Message": "New product added sucesfully",
                    "Product": product_schema.dump(new_product)}), 201

# Get all products (GET)

@app.route("/products", methods=["GET"])
def get_all_products(): 
    query = select(Products)
    result = db.session.execute(query).scalars()
    products = result.all()  # Variable renamed to 'products'
    return products_schema.jsonify(products), 200


# Get product by ID (GET)

@app.route('/products/<int:id>', methods=["GET"])
def get_product(id):
    query = select(Products).where(Products.id == id)
    result = db.session.execute(query).scalars().first()  # Variable renamed to 'product'

    if result is None:
        return jsonify({"Error": "Product not found"}), 404
    
    return product_schema.jsonify(result), 200  # serializes products into JSON format, returns user and status code 200

# Update product (PUT)

@app.route('/products/<int:id>', methods=["PUT"])
def update_product(id):
    product = db.session.get(Products, id)  # Variable renamed to 'product'

    if not product:
        return jsonify({"Message": "Invalid product id"}), 400
    
    try:
        product_data = product_schema.load(request.json)
    except ValidationError as e:
        return jsonify(e.messages), 400
    
    product.product_name = product_data['product_name']
    product.price = product_data['price']

    db.session.commit()
    return product_schema.jsonify(product), 200  



# Delete product (DELETE)

@app.route("/products/<int:id>", methods=["DELETE"])
def delete_product(id):
    product = db.session.get(Products, id)  # Variable renamed to 'product'

    if not product:
        return jsonify({"Message": "Invalid product id"}), 400
    
    db.session.delete(product)
    db.session.commit()
    return jsonify({"Message": "Product deleted successfully"}), 200
#========== API ROUTES: Orders ==========
# Create new order (POST)

@app.route("/orders", methods=["POST"])
def add_order():
    try:
        order_data = order_schema.load(request.json)
    except ValidationError as e:
        return jsonify(e.messages), 400
    
    # retrieve customer by id
    customer = db.session.get(Customer, order_data["customer_id"])

    # check if customer exists
    if customer:
        new_order = Orders(order_date=order_data['order_date'], customer_id = order_data['customer_id'])

        db.session.add(new_order)
        db.session.commit()

        return jsonify({"Message": "New order placed successfully",
                        "Order": order_schema.dump(new_order)}), 201
    else:
        return jsonify({"Message": "Invalid customer id"}), 400
    
# Add item to order (POST)
@app.route("/orders/<int:order_id>/add_product/<int:product_id>", methods=["PUT"])
def add_product(order_id, product_id):
    order = db.session.get(Orders, order_id)  # Corrected 'id' to 'order_id'
    product = db.session.get(Products, product_id)

    if order and product:
        if product not in order.products:
            order.products.append(product)
            db.session.commit()
            return jsonify({"Message": "Successfully added item to order."}), 200
        else:
            return jsonify({"Message": "Product already in order."}), 400
    else:
        return jsonify({"Message": "Invalid order or product id"}), 400
    
# Get all orders (GET)

@app.route("/orders", methods=["GET"])
def get_orders():
    query = select(Orders)
    result = db.session.execute(query).scalars()
    orders = result.all()  # Variable renamed to 'orders'
    return orders_schema.jsonify(orders), 200

# Get all products for an order
@app.route('/orders/<int:order_id>/products', methods=['GET'])
def get_order_products(order_id):
    # Get the order by ID
    order = db.session.get(Orders, order_id)
    
    if not order:
        return jsonify({"error": "Order not found"}), 404
    
    # Get the products associated with the order
    products = order.products
    
    return products_schema.jsonify(products), 200

# Delete order (DELETE)

@app.route("/orders/<int:id>", methods=["DELETE"])
def delete_order(id):
    Order = db.session.get(Order, id) # retrieves order with specified id from DB

    if not Order:
        return jsonify({"Message": "Invalid order id"}), 400
    
    db.session.delete(Order) # deletes order from DB
    db.session.commit() # commits changes to DB
    return jsonify({"Message": "Order deleted successfully"}), 200 # returns success message and status code 200


if __name__ == '__main__':
    app.run(debug=True) # run the app in debug mode