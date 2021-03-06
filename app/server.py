from starlette.applications import Starlette
from starlette.responses import HTMLResponse, JSONResponse
from starlette.staticfiles import StaticFiles
from starlette.middleware.cors import CORSMiddleware
import uvicorn, aiohttp, asyncio
from io import BytesIO

from fastai import *
from fastai.vision import *

from functools import partial
import pickle

model_file_url = 'https://drive.google.com/uc?export=download&id=15NSQ3zqLBrSjpClh8Un-sA2wMUh9M2gT'
model_file_name = 'korean-food-classifier'
classes = ['bibim_guksu',
 'bibimbap',
 'bokkeum',
 'bulgogi',
 'dak_galbi',
 'galbi',
 'gimbap',
 'gukbap',
 'jajangmyeon',
 'japchae',
 'jeon',
 'jjigae',
 'kimchi',
 'kimchi_fried_rice',
 'mandu',
 'naengmyeon',
 'namul',
 'samgyeopsal',
 'tteok_bokki',
 'yukhoe']
path = Path(__file__).parent

app = Starlette()
app.add_middleware(CORSMiddleware, allow_origins=['*'], allow_headers=['X-Requested-With', 'Content-Type'])
app.mount('/static', StaticFiles(directory='app/static'))

async def download_file(url, dest):
    if dest.exists(): return
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            data = await response.read()
            with open(dest, 'wb') as f: f.write(data)

async def setup_learner():
    await download_file(model_file_url, path/'models'/f'{model_file_name}.pkl')
    #data_bunch = ImageDataBunch.single_from_classes(path, classes,
    #    ds_tfms=get_transforms(), size=224).normalize(imagenet_stats)
    #learn = cnn_learner(data_bunch, models.resnet50, pretrained=False)
    #learn.load(model_file_name)
    pickle.load = partial(pickle.load, encoding='latin1')
    pickle.Unpickler = partial(pickle.Unpickler, encoding='latin1')
    learn = load_learner(path/'models', f'{model_file_name}.pkl')    
    return learn

loop = asyncio.get_event_loop()
tasks = [asyncio.ensure_future(setup_learner())]
learn = loop.run_until_complete(asyncio.gather(*tasks))[0]
loop.close()

@app.route('/')
def index(request):
    html = path/'view'/'index.html'
    return HTMLResponse(html.open().read())

@app.route('/analyze', methods=['POST'])
async def analyze(request):
    data = await request.form()
    img_bytes = await (data['file'].read())
    img = open_image(BytesIO(img_bytes))
    return JSONResponse({'result': str(learn.predict(img)[0])})

if __name__ == '__main__':
    if 'serve' in sys.argv: uvicorn.run(app, host='0.0.0.0', port=8080)

