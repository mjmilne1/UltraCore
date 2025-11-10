from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from ultracore.domains.loan.api import router as loan_router
from ultracore.data_mesh.api import router as data_mesh_router
from ultracore.infrastructure.event_store.api import router as event_store_router
from ultracore.infrastructure.event_store.store import get_event_store

app = FastAPI(
    title='UltraCore - Event Sourced Banking',
    version='1.0.0',
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)

app.include_router(loan_router, prefix='/api/v1/loans', tags=['Loans'])
app.include_router(data_mesh_router)
app.include_router(event_store_router)


@app.on_event('startup')
async def startup():
    store = get_event_store()
    await store.initialize()
    print('Event Store initialized')


@app.get('/')
async def root():
    return {
        'service': 'UltraCore',
        'company': 'TuringDynamics',
        'version': '1.0.0',
        'architecture': 'Event Sourcing + Data Mesh',
        'event_store': '/api/v1/events',
        'data_mesh': '/api/v1/data-mesh/catalog'
    }


@app.get('/health')
async def health():
    return {'status': 'healthy'}


def main():
    uvicorn.run('ultracore.main:app', host='0.0.0.0', port=8000, reload=True)


if __name__ == '__main__':
    main()
