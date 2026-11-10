"""Пример главы 3: Blueprint и документация Flasgger."""
from flask import Flask, Blueprint, jsonify
from flasgger import Swagger

app = Flask(__name__)
app.json.ensure_ascii = False
Swagger(app)
sitepart = Blueprint('sitepart', __name__)


@app.get('/info/<about>/')
def info(about):
    """Сведения о примере.
    ---
    parameters:
      - name: about
        in: path
        type: string
        required: true
        enum: [all, version, author, year]
    responses:
      200:
        description: Сведения о приложении
      404:
        description: Неизвестное поле
    """
    data = dict(version='1.0', author='Артюхов Д. А.', year='2026')
    if about == 'all':
        return jsonify(data)
    if about not in data:
        return jsonify(message='Поле не найдено'), 404
    return jsonify({about: data[about]})


@sitepart.get('/colors/<palette>/')
def colors(palette):
    """Цвета выбранной палитры.
    ---
    parameters:
      - name: palette
        in: path
        type: string
        required: true
        enum: [all, rgb, cmyk]
    responses:
      200:
        description: Список цветов
      404:
        description: Палитра не найдена
    """
    data = dict(rgb=['red', 'green', 'blue'], cmyk=['cyan', 'magenta', 'yellow', 'black'])
    if palette == 'all':
        return jsonify(data)
    if palette not in data:
        return jsonify(message='Палитра не найдена'), 404
    return jsonify({palette: data[palette]})


app.register_blueprint(sitepart, url_prefix='/sitepart')
if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8038, debug=False)
