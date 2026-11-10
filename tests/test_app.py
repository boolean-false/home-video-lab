import unittest
import app as module
from examples.flasgger_example import app as flasgger_app
from examples.restx_example import app as example_app


class FilmTests(unittest.TestCase):
    def setUp(self):
        module.reset_data()
        self.client = module.app.test_client()
        self.film = dict(title='Новый фильм', genre='Драма', year=2021, duration=120, rating=6.5)

    def test_create_read_update_delete(self):
        response = self.client.post('/api/films/', json=self.film)
        self.assertEqual(response.status_code, 201)
        number = response.json['id']
        self.assertEqual(self.client.get(f'/api/films/{number}').json['duration'], 120)
        changed = dict(self.film, duration=125)
        response = self.client.put(f'/api/films/{number}', json=changed)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json['duration'], 125)
        self.assertEqual(response.json['id'], number)
        response = self.client.delete(f'/api/films/{number}')
        self.assertEqual(response.status_code, 204)
        self.assertEqual(response.data, b'')
        self.assertEqual(self.client.get(f'/api/films/{number}').status_code, 404)

    def test_sort_all_fields(self):
        expected = {'id': [1,2,3], 'title': [3,2,1], 'genre': [1,2,3],
                    'year': [1,2,3], 'duration': [1,2,3], 'rating': [1,2,3]}
        for key, ids in expected.items():
            for order in ['asc', 'desc']:
                with self.subTest(key=key, order=order):
                    response = self.client.get(f'/api/films/?sort={key}&order={order}')
                    self.assertEqual(response.status_code, 200)
                    self.assertEqual([v['id'] for v in response.json], ids if order=='asc' else ids[::-1])

    def test_statistics_all_fields(self):
        for key, values in {'id': (1,3,2), 'year': (2020,2024,2022),
                            'duration': (90,110,100), 'rating': (7,9,8)}.items():
            with self.subTest(key=key):
                r = self.client.get('/api/films/stats?field='+key)
                self.assertEqual(r.status_code, 200)
                self.assertEqual((r.json['min'],r.json['max'],r.json['mean']), values)

    def test_statistics_after_changes(self):
        self.client.post('/api/films/', json=self.film)
        self.assertEqual(self.client.get('/api/films/stats').json['mean'],105)
        self.client.put('/api/films/4', json=dict(self.film,duration=140))
        self.assertEqual(self.client.get('/api/films/stats').json['mean'],110)
        self.client.delete('/api/films/4')
        self.assertEqual(self.client.get('/api/films/stats').json['mean'],100)

    def test_empty_collection(self):
        for i in [1,2,3]: self.client.delete('/api/films/'+str(i))
        self.assertEqual(self.client.get('/api/films/').json, [])
        self.assertEqual(self.client.get('/api/films/stats').json,
                         dict(field='duration',count=0,min=None,max=None,mean=None))

    def test_identifiers_not_reused(self):
        self.client.delete('/api/films/3')
        self.assertEqual(self.client.post('/api/films/',json=self.film).json['id'],4)

    def test_invalid_fields(self):
        for key,value in [('title',' '),('genre','x'*41),('year',1800),('year',2020.5),
                          ('duration',0),('duration',True),('rating',11),('rating','8'),('rating',False)]:
            for method,url in [('post','/api/films/'),('put','/api/films/1')]:
                with self.subTest(key=key,value=value,method=method):
                    response=getattr(self.client,method)(url,json=dict(self.film,**{key:value}))
                    self.assertEqual(response.status_code,400)
        self.assertEqual(len(self.client.get('/api/films/').json),3)
        self.assertEqual(self.client.get('/api/films/1').json['title'],'Первый рейс')

    def test_invalid_json_shape(self):
        for data in [None, [], {}, dict(self.film,id=8), dict(title='Фильм')]:
            with self.subTest(data=data):
                r=self.client.post('/api/films/',json=data,content_type='application/json')
                self.assertEqual(r.status_code,400)

    def test_non_finite(self):
        for text in ['NaN','Infinity','-Infinity']:
            data='{"title":"A","genre":"B","year":2020,"duration":90,"rating":'+text+'}'
            self.assertEqual(self.client.post('/api/films/',data=data,content_type='application/json').status_code,400)

    def test_missing_and_unknown(self):
        self.assertEqual(self.client.put('/api/films/999',json=self.film).status_code,404)
        self.assertEqual(self.client.delete('/api/films/999').status_code,404)
        self.assertEqual(self.client.get('/api/films/?sort=unknown').status_code,400)
        self.assertEqual(self.client.get('/api/films/?order=unknown').status_code,400)
        self.assertEqual(self.client.get('/api/films/stats?field=title').status_code,400)

    def test_media_type_and_size(self):
        self.assertEqual(self.client.post('/api/films/',data='bad').status_code,415)
        self.assertEqual(self.client.post('/api/films/',data='x'*17000,content_type='application/json').status_code,413)

    def test_swagger_and_page(self):
        self.assertEqual(self.client.get('/').status_code,200)
        self.assertEqual(self.client.get('/docs/').status_code,200)
        spec=self.client.get('/api/swagger.json').json
        self.assertEqual(spec['swagger'],'2.0')
        self.assertEqual(spec['basePath'],'/api')
        self.assertEqual(set(spec['paths']['/films/']),{'get','post'})
        self.assertEqual(set(spec['paths']['/films/{film_id}']),{'parameters','get','put','delete'})
        self.assertIn('/films/stats',spec['paths'])


class ChapterExamples(unittest.TestCase):
    def test_flasgger(self):
        c=flasgger_app.test_client()
        self.assertEqual(c.get('/info/version/').json,{'version':'1.0'})
        self.assertEqual(c.get('/sitepart/colors/rgb/').json,{'rgb':['red','green','blue']})
        self.assertEqual(c.get('/sitepart/colors/no/').status_code,404)
        self.assertEqual(c.get('/apidocs/').status_code,200)
        self.assertIn('/info/{about}/',c.get('/apispec_1.json').json['paths'])

    def test_restx_examples(self):
        c=example_app.test_client()
        self.assertEqual(c.get('/main/').json,{'status':'Got new data'})
        self.assertEqual(c.post('/main/').json,{'status':'Posted new data'})
        self.assertEqual(c.get('/part/1111').json,{'id':'1111','name':'Alex'})
        self.assertEqual(c.get('/part/2').status_code,404)
        self.assertEqual(c.get('/templ/').data,b'template')
        self.assertEqual(c.post('/list/',json={'len':3,'array':[11,5,3]}).status_code,200)
        self.assertEqual(c.get('/list/').json,{'len':3,'array':[11,5,3]})
        self.assertEqual(c.get('/list/minmax').json,{'min':3,'max':11})
        self.assertEqual(c.post('/list/',json={'len':2,'array':[1]}).status_code,400)
        r=c.get('/list/makerand?len=7&minval=1&maxval=12')
        self.assertEqual(r.status_code,200)
        self.assertEqual(len(r.json['array']),7)
        self.assertTrue(all(1<=v<=12 for v in r.json['array']))


if __name__=='__main__':
    unittest.main()
