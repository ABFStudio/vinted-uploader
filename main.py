from flask import Flask, render_template, redirect, request, url_for, flash
from flask_sqlalchemy import SQLAlchemy
import secrets

from utils import (
    parse_type,
    parse_brand,
    parse_quality,
    generate_code,
    generate_folder_name,
    count_item,
    average_price,
    list_or_convert_to_list,
    get_quantity,
    ALL_TYPES
)

db = SQLAlchemy()

class VintedItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    type = db.Column(db.String(100), nullable=False)
    color = db.Column(db.String(100), nullable=False)
    brand = db.Column(db.String(100), nullable=False)
    size = db.Column(db.String(5), nullable=False)
    quality = db.Column(db.String(2), nullable=False)
    code = db.Column(db.String(10), unique=True)
    price = db.Column(db.Float, nullable=True, default=0.0)

app = Flask(__name__)
app.config['SECRET_KEY'] = secrets.token_urlsafe(40)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///db.sqlite3'

db.init_app(app)

with app.app_context():
    db.create_all()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/items/upload', methods=['POST'])
def upload_item():
    type = parse_type(request.form.get('type'))
    brand = parse_brand(request.form.get('brand'))
    color = request.form.get('color').lower()
    size = request.form.get('size')
    quality = parse_quality(request.form.get('quality'))

    if type == "" or brand == "" or color == "" or quality == "" or size == "":
        flash('Tous les champs sont requis!', category='error')
        folder_name = ''
        code = ''
    else:
        folder_name = generate_folder_name(type, color, size, brand, quality)
        code = generate_code(folder_name)
        code_list = VintedItem.query.with_entities(VintedItem.code).all()
        for c in code_list:
            if code == c[0]:
                if code[-1].isdigit():
                    # the code already existed and we increment the counter at the end of the code
                    code = list(code)
                    code[-1] = str(int(code[-1]) + 1)
                    code = ''.join(code)
                else:
                    code += '2'
        new_item = VintedItem(type=type, brand=brand, size=size, color=color, quality=quality, code=code)
        db.session.add(new_item)
        db.session.commit()
        flash('Item ajouté!', category='success')
    if folder_name == '' and code == '':
        return render_template('index.html', folder_name='')
    return render_template('index.html', folder_name=folder_name + '_' + code)

@app.route('/items/edit/price/<id>', methods=['POST'])
def update_item_price(id):
    item = VintedItem.query.filter_by(id=id).first()
    item.price = request.form.get('price')
    db.session.commit()
    return redirect(url_for('all_items'))

@app.route('/items/all')
def all_items():
    return render_template('all_items.html', items=VintedItem.query.all())

@app.route('/items/delete/<id>', methods=['DELETE'])
def delete_item(id):
    VintedItem.query.filter_by(id=id).delete()
    db.session.commit()
    return render_template('all_items.html', items=VintedItem.query.all())

@app.route('/items/delete/all', methods=['DELETE'])
def delete_all_items():
    db.session.query(VintedItem).delete()
    db.session.commit()
    return redirect(url_for('all_items'))

@app.route('/stats')
def stats():
    stats_list = {}
    for type in ALL_TYPES:
        price_list = [item.price for item in VintedItem.query.filter_by(type=type).all()]
        stats_list[type] = {
            'name': type,
            'total': count_item(VintedItem, type),
            'average_price': average_price(price_list)
        }
    quantities = {type: get_quantity(VintedItem, type) for type in ALL_TYPES}
    return render_template('stats.html', stats=stats_list, quantities=quantities)

@app.route('/items/filter', methods=['POST'])
def filter_items():
    request_type = request.form.get('type')
    request_brand = request.form.get('brand')
    request_color = request.form.get('color')
    request_size = request.form.get('size')
    request_quality = request.form.get('quality')

    _type = parse_type(request_type)
    brand = parse_brand(request_brand)
    quality = parse_quality(request_quality)

    if _type == '': _type = VintedItem.type
    else: _type = VintedItem.query.filter_by(type=_type).all()

    if brand == '': brand = VintedItem.brand
    else: brand = VintedItem.query.filter_by(brand=brand).all()

    if request_color == '': color = VintedItem.color
    else: color = VintedItem.query.filter_by(color=request_color.lower()).all()

    if request_size == '': size = VintedItem.size
    else: size = VintedItem.query.filter_by(size=request_size).all()

    if request_quality == '': quality = VintedItem.quality
    else: quality = VintedItem.query.filter_by(quality=quality).all()

    types     = list_or_convert_to_list(_type,   VintedItem)
    brands    = list_or_convert_to_list(brand,   VintedItem)
    colors    = list_or_convert_to_list(color,   VintedItem)
    sizes     = list_or_convert_to_list(size,    VintedItem)
    qualities = list_or_convert_to_list(quality, VintedItem)

    items_list = {
        'types': types,
        'brands': brands,
        'colors': colors,
        'sizes': sizes,
        'qualities': qualities
    }

    quantities = {type: get_quantity(VintedItem, type) for type in ALL_TYPES}

    return render_template('filters.html', items=items_list, quantities=quantities)

if __name__ == '__main__':
    app.run(debug=True, port=8080)
