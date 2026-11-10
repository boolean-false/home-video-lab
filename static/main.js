const form = document.getElementById('film-form');
const message = document.getElementById('message');
let selectedId = null;

async function apiRequest(url, method = 'GET', data = null) {
  const options = {method};
  if (data !== null) {
    options.headers = {'Content-Type': 'application/json'};
    options.body = JSON.stringify(data);
  }
  const response = await fetch(url, options);
  if (response.status === 204) return null;
  const result = await response.json();
  if (!response.ok) throw new Error(result.message || 'Ошибка запроса');
  return result;
}

function cancelEdit() {
  selectedId = null;
  form.reset();
  document.getElementById('form-title').textContent = 'Добавить фильм';
}

async function loadStatistics() {
  const field = document.getElementById('field').value;
  const data = await apiRequest('/api/films/stats?field=' + field);
  document.getElementById('stats').textContent = data.count
    ? `Записей: ${data.count}. Минимум: ${data.min}. Максимум: ${data.max}. Среднее: ${data.mean}.`
    : 'Нет записей для расчета.';
}

async function loadFilms() {
  try {
    const sort = document.getElementById('sort').value;
    const order = document.getElementById('order').value;
    const films = await apiRequest(`/api/films/?sort=${sort}&order=${order}`);
    const body = document.getElementById('films');
    body.replaceChildren();
    for (const film of films) {
      const row = body.insertRow();
      for (const key of ['id', 'title', 'genre', 'year', 'duration', 'rating']) {
        row.insertCell().textContent = film[key];
      }
      const actions = row.insertCell();
      actions.className = 'text-nowrap';
      const edit = document.createElement('button');
      edit.className = 'btn btn-sm btn-outline-primary';
      edit.textContent = 'Изменить';
      edit.onclick = () => {
        selectedId = film.id;
        for (const key of ['title', 'genre', 'year', 'duration', 'rating']) form.elements[key].value = film[key];
        document.getElementById('form-title').textContent = 'Изменить фильм № ' + film.id;
      };
      const remove = document.createElement('button');
      remove.className = 'btn btn-sm btn-outline-danger';
      remove.textContent = 'Удалить';
      remove.onclick = async () => {
        try {
          await apiRequest('/api/films/' + film.id, 'DELETE');
          if (selectedId === film.id) cancelEdit();
          message.textContent = 'Фильм удален.';
          await loadFilms();
        } catch (error) { message.textContent = error.message; }
      };
      actions.append(edit, ' ', remove);
    }
    await loadStatistics();
  } catch (error) { message.textContent = error.message; }
}

form.onsubmit = async event => {
  event.preventDefault();
  const data = Object.fromEntries(new FormData(form));
  for (const key of ['year', 'duration', 'rating']) data[key] = Number(data[key]);
  try {
    await apiRequest(selectedId === null ? '/api/films/' : '/api/films/' + selectedId,
      selectedId === null ? 'POST' : 'PUT', data);
    message.textContent = selectedId === null ? 'Фильм добавлен.' : 'Изменения сохранены.';
    cancelEdit();
    await loadFilms();
  } catch (error) { message.textContent = error.message; }
};
document.getElementById('cancel').onclick = cancelEdit;
document.getElementById('refresh').onclick = loadFilms;
document.getElementById('sort').onchange = loadFilms;
document.getElementById('order').onchange = loadFilms;
document.getElementById('field').onchange = () => loadStatistics().catch(error => { message.textContent = error.message; });
loadFilms();
