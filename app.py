"""ЛР2. Домашняя видеотека, вариант 16."""
import math
import os
from threading import Lock

from flask import Flask, render_template, request
from flask_restx import Api, Resource, fields

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024
app.config['RESTX_MASK_SWAGGER'] = False
app.json.ensure_ascii = False
api = Api(app, version='1.0', title='Домашняя видеотека',
          description='Учебный сервис учета фильмов. Вариант 16.', doc='/docs/', prefix='/api')
ns = api.namespace('films', description='Фильмы')
lock = Lock()
films = []
next_id = 1
names = ['id', 'title', 'genre', 'year', 'duration', 'rating']
numeric = ['id', 'year', 'duration', 'rating']
input_model = ns.model('FilmInput', {
    'title': fields.String(required=True, example='Новый фильм', description='Название, 1-100 символов'),
    'genre': fields.String(required=True, example='Драма', description='Жанр, 1-40 символов'),
    'year': fields.Integer(required=True, min=1888, max=2100, example=2021, description='Год выпуска'),
    'duration': fields.Integer(required=True, min=1, max=1000, example=120, description='Длительность в минутах'),
    'rating': fields.Float(required=True, min=0, max=10, example=6.5, description='Личная оценка от 0 до 10'),
}, strict=True)
film_model = ns.inherit('Film', input_model, {
    'id': fields.Integer(description='Номер записи, назначается сервером'),
})
stats_model = ns.model('Statistics', {
    'field': fields.String, 'count': fields.Integer,
    'min': fields.Float, 'max': fields.Float, 'mean': fields.Float,
})


def reset_data():
    """Начальные учебные записи загружаются при запуске сервиса."""
    global films, next_id
    films = [
        dict(id=1, title='Первый рейс', genre='Драма', year=2020, duration=90, rating=7.0),
        dict(id=2, title='Летние каникулы', genre='Комедия', year=2022, duration=100, rating=8.0),
        dict(id=3, title='Далекая планета', genre='Фантастика', year=2024, duration=110, rating=9.0),
    ]
    next_id = 4


def read_film():
    """Проверяем данные до изменения списка."""
    if not request.is_json:
        ns.abort(415, 'Нужен Content-Type: application/json.')
    data = request.get_json(silent=True)
    if not isinstance(data, dict) or set(data) != set(names[1:]):
        ns.abort(400, 'Нужны только поля title, genre, year, duration, rating.')
    for key, limit in [('title', 100), ('genre', 40)]:
        if not isinstance(data[key], str) or not 1 <= len(data[key].strip()) <= limit:
            ns.abort(400, f'Поле {key}: от 1 до {limit} символов.')
        data[key] = data[key].strip()
    for key, low, high in [('year', 1888, 2100), ('duration', 1, 1000)]:
        if type(data[key]) is not int or not low <= data[key] <= high:
            ns.abort(400, f'Поле {key}: целое число от {low} до {high}.')
    rating = data['rating']
    if type(rating) not in (int, float) or not math.isfinite(rating) or not 0 <= rating <= 10:
        ns.abort(400, 'Оценка должна быть числом от 0 до 10.')
    return data


def find_film(film_id):
    for film in films:
        if film['id'] == film_id:
            return film
    ns.abort(404, 'Фильм не найден.')


@app.get('/')
def index():
    return render_template('index.html')


@ns.route('/')
class FilmList(Resource):
    @ns.doc(params={'sort': {'description': 'Поле сортировки', 'enum': names, 'default': 'id'},
                    'order': {'description': 'Порядок', 'enum': ['asc', 'desc'], 'default': 'asc'}})
    @ns.marshal_list_with(film_model)
    @ns.response(400, 'Неверные параметры сортировки')
    def get(self):
        """Получить список с сортировкой по любому полю."""
        key = request.args.get('sort', 'id')
        order = request.args.get('order', 'asc')
        if key not in names or order not in ['asc', 'desc']:
            ns.abort(400, 'Неверное поле или направление сортировки.')
        with lock:
            return sorted((f.copy() for f in films),
                          key=lambda f: f[key].casefold() if isinstance(f[key], str) else f[key],
                          reverse=order == 'desc')

    @ns.expect(input_model)
    @ns.marshal_with(film_model, code=201)
    @ns.response(400, 'Некорректные данные')
    @ns.response(415, 'Нужен JSON')
    @ns.response(409, 'Список заполнен')
    def post(self):
        """Добавить фильм. Номер назначается автоматически."""
        global next_id
        data = read_film()
        with lock:
            if len(films) >= 1000:
                ns.abort(409, 'В учебном списке допускается до 1000 фильмов.')
            film = dict(id=next_id, **data)
            next_id += 1
            films.append(film)
            return film.copy(), 201


@ns.route('/<int:film_id>')
@ns.param('film_id', 'Номер фильма')
@ns.response(404, 'Фильм не найден')
class FilmItem(Resource):
    @ns.marshal_with(film_model)
    def get(self, film_id):
        """Получить один фильм."""
        with lock:
            return find_film(film_id).copy()

    @ns.expect(input_model)
    @ns.marshal_with(film_model)
    @ns.response(400, 'Некорректные данные')
    @ns.response(415, 'Нужен JSON')
    def put(self, film_id):
        """Заменить данные фильма, сохранив его номер."""
        data = read_film()
        with lock:
            film = find_film(film_id)
            film.update(data)
            return film.copy()

    @ns.response(204, 'Фильм удален')
    def delete(self, film_id):
        """Удалить фильм по номеру."""
        with lock:
            films.remove(find_film(film_id))
        return '', 204


@ns.route('/stats')
class Statistics(Resource):
    @ns.doc(params={'field': {'description': 'Числовое поле', 'enum': numeric, 'default': 'duration'}})
    @ns.marshal_with(stats_model)
    @ns.response(400, 'Нужно числовое поле')
    def get(self):
        """Найти минимум, максимум и среднее."""
        key = request.args.get('field', 'duration')
        if key not in numeric:
            ns.abort(400, 'Выберите id, year, duration или rating.')
        with lock:
            values = [f[key] for f in films]
        return dict(field=key, count=len(values),
                    min=min(values) if values else None,
                    max=max(values) if values else None,
                    mean=round(sum(values) / len(values), 4) if values else None)


reset_data()

if __name__ == '__main__':
    from waitress import serve
    serve(app, host='127.0.0.1', port=int(os.environ.get('PORT', '8037')), threads=2)
