from flask import Flask, request, url_for, render_template, redirect,jsonify
import numpy as np
import cv2
import os
from pyzbar.pyzbar import decode
from multiprocessing import Value

# Init

app = Flask(__name__)
app.config['DEBUG'] = True
app.secret_key = 'sdfhj43uop23opjuhjg234jghds8'
app.jinja_env.globals.update(zip=zip)

# Variables

products = [
    {"id": 1, "name": "Винты", "price": 2.5},
    {"id": 2, "name": "Гайки", "price": 1.5},
    {"id": 3, "name": "Шайбы", "price": 0.75},
    {"id": 4, "name": "Шпильки", "price": 1.0},
    {"id": 5, "name": "Подшипники", "price": 5.0},
    {"id": 6, "name": "Линейные направляющие", "price": 8.0},
    {"id": 7, "name": "Валы", "price": 4.5},
    {"id": 8, "name": "Двигатели", "price": 20.0},
    {"id": 9, "name": "Датчики", "price": 15.0},
]

cart = []
state = 0


# Site routes

@app.route('/')
def index():
    return render_template('index.html', products=products)

@app.route('/cart')
def view_cart():
    total_price = sum(item['price'] for item in cart)
    return render_template('cart.html', cart=cart, total_price=total_price)

# Image-processing functions

counter = Value('i', 0)

def save_img(img):
	with counter.get_lock():
		counter.value += 1
		count = counter.value
	img_dir = "esp32_imgs"
	if not os.path.isdir(img_dir):
		os.mkdir(img_dir)
	cv2.imwrite(os.path.join(img_dir,"img_"+str(count)+".jpg"), img)
	# print("Image Saved", end="\n") # debug

def decode_qr_code(img):
	gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
	decoded_objects = decode(gray)
	for obj in decoded_objects:
		print("Data:", obj.data.decode('utf-8'))
		print("Type:", obj.type); 
		return obj.data.decode('utf-8')
	return 0

# API

@app.route('/api/get_cart', methods=['POST','GET'])
def get_cart():
	s = ""
	for i in cart:
		s += str(i["id"])
	return s

@app.route("/api/off", methods=['POST','GET'])
def set_state_off():
	global state
	state = 0
	return jsonify({'status': 'success', 'message': 'State changed'})

@app.route("/api/on", methods=['POST','GET'])
def set_state_on():
	global state
	state = 1
	return jsonify({'status': 'success', 'message': 'State changed'})

@app.route('/api/return', methods=['POST','GET'])
def set_state_return():
	global state
	state = 2
	return jsonify({'status': 'success', 'message': 'State changed'})

@app.route("/api/get_state", methods=['POST','GET']) 	
def get_state():
	return str(state)

@app.route('/api/add_to_cart/<int:product_id>', methods=['GET'])
def add_to_cart_ajax(product_id):
    product = next((p for p in products if p["id"] == product_id), None)
    if product and product not in cart:
        cart.append(product)

    return jsonify({'status': 'success', 'message': 'Product added to cart'})

@app.route('/api/upload', methods=['POST','GET'])
def upload():
	received = request
	img = None
	if received.files:
		print(received.files['imageFile'])
		# convert string of image data to uint8
		file  = received.files['imageFile']
		nparr = np.fromstring(file.read(), np.uint8)
		# decode image
		img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
		
		result = decode_qr_code(img)
		save_img(img)

		return str(result), 201
	else:
		return "[FAILED] Image Not Received", 204

# Running

if __name__ == '__main__':  
    app.run(debug = True, host='192.168.1.15', port=8723)