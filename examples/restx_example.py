"""Примеры главы 3 с Flask-RESTX: ресурсы, модели и массивы."""
import random
import math
from flask import Flask, Blueprint, request
from flask_restx import Api, Resource, fields

app = Flask(__name__)
api = Api(app, title='Примеры главы 3', doc='/docs/')
main = api.namespace('main', description='GET и POST')
part = api.namespace('part', description='Поиск по номеру')
lists = api.namespace('list', description='Числовые массивы')
array = [1.0]
array_model = api.model('Array', {
    'len': fields.Integer(required=True),
    'array': fields.List(fields.Float, required=True),
})
person_model = api.model('Person', {'id': fields.String, 'name': fields.String})
minmax_model = api.model('MinMax', {'min': fields.Float, 'max': fields.Float})


@main.route('/')
class Main(Resource):
    def get(self):
        """Пример GET."""
        return {'status': 'Got new data'}

    def post(self):
        """Пример POST."""
        return {'status': 'Posted new data'}


@part.route('/')
class People(Resource):
    @part.marshal_list_with(person_model)
    def get(self):
        """Получить список."""
        return [{'id': '1111', 'name': 'Alex'}]


@part.route('/<string:person_id>')
class Person(Resource):
    @part.marshal_with(person_model)
    @part.response(404, 'Запись не найдена')
    def get(self, person_id):
        """Найти запись по номеру."""
        if person_id != '1111':
            part.abort(404, 'Запись не найдена')
        return {'id': '1111', 'name': 'Alex'}


@lists.route('/')
class Array(Resource):
    @lists.marshal_with(array_model)
    def get(self):
        """Получить массив."""
        return {'len': len(array), 'array': array}

    @lists.expect(array_model, validate=True)
    @lists.marshal_with(array_model)
    def post(self):
        """Заменить массив."""
        global array
        data = api.payload
        if type(data['len']) is not int or data['len'] != len(data['array']) or not 1 <= data['len'] <= 1000:
            lists.abort(400, 'Неверная длина массива')
        if any(type(v) not in (int, float) or not math.isfinite(v) for v in data['array']):
            lists.abort(400, 'Нужны конечные числа')
        array = data['array'][:]
        return {'len': len(array), 'array': array}


@lists.route('/minmax')
class MinMax(Resource):
    @lists.marshal_with(minmax_model)
    def get(self):
        """Минимум и максимум массива."""
        return {'min': min(array), 'max': max(array)}


@lists.route('/makerand')
class RandomArray(Resource):
    @lists.doc(params={'len': 'Размер массива', 'minval': 'Нижняя граница', 'maxval': 'Верхняя граница'})
    @lists.marshal_with(array_model)
    def get(self):
        """Создать массив случайных чисел."""
        try:
            size = int(request.args['len'])
            low, high = float(request.args['minval']), float(request.args['maxval'])
        except (KeyError, ValueError):
            lists.abort(400, 'Нужны len, minval и maxval')
        if not 1 <= size <= 1000 or not math.isfinite(low) or not math.isfinite(high) or low > high:
            lists.abort(400, 'Неверный размер или границы')
        values = [random.uniform(low, high) for _ in range(size)]
        return {'len': size, 'array': values}


templ = Blueprint('templ', __name__)
@templ.get('/')
def index():
    return 'template'

app.register_blueprint(templ, url_prefix='/templ')
if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8039, debug=False)
