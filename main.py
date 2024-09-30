import os
from contextlib import asynccontextmanager
from mangum import Mangum

from fastapi import Depends, FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, HTMLResponse

from routers.admin_router import admin_router
from routers.users_router import users_router
from routers.lessons_router import lessons_router
from database import create_database
from database import (
   EntityNotFoundException,
   UnrelatedEntitiesException,
   InvalidRequestExcpetion,
   PermissionsException,
   DuplicateEntitiyException
)

@asynccontextmanager
async def lifespan(app: FastAPI):
    create_database()
    yield


app = FastAPI(
  title="Signable",
  description="An educational platform that provides interactive and structured lessons for learning American Sign Language (ASL)",
  version="0.1.0",
  lifespan=lifespan
)

app.add_middleware(
   CORSMiddleware,
    allow_origins=[
       "http://localhost:5173",
       "http://localhost:5174",
       "https://signable-ffg0eegcfngdgubn.westus2-01.azurewebsites.net",
       "https://tv",
       "https://www.tv",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(users_router)
app.include_router(lessons_router)
app.include_router(admin_router)

@app.get("/", include_in_schema=False)
def default() -> str:
  return HTMLResponse(
    content=f"""
      <html>
        <body>
          <h2>{app.title}</h2>
          <p>{app.description}</p>
          <h2>API Docs</h2>
          <ul>
            <li><a href="/docs">Swagger</a></li>
            <li><a href="/redoc">ReDoc</a></li>
          </ul>
        </body>
      </html>
    """
  )

@app.exception_handler(EntityNotFoundException)
def handle_entity_not_found(
    _request: Request,
    exception: EntityNotFoundException,
) -> JSONResponse:
    return JSONResponse(
        status_code=404,
        content={
            "detail": {
                "type": "entity_not_found",
                "entity_name": exception.entity_name,
                "entity_id": exception.entity_id,
            },
        },
    )

@app.exception_handler(UnrelatedEntitiesException)
def handle_unrelated_entities(
      _request: Request,
      exception: UnrelatedEntitiesException,
) -> JSONResponse:
   return JSONResponse(
      status_code=404,
      content={
         "detail": {
            "type": "relation_not_found",
            "entity_name_1": exception.first_entity,
            "entity_id_1": exception.first_id,
            "entity_name_2": exception.second_entity,
            "entity_id_2": exception.second_id
         }
      }
   )

@app.exception_handler(InvalidRequestExcpetion)
def handle_unrelated_entities(
      _request: Request,
      exception: InvalidRequestExcpetion,
) -> JSONResponse:
   return JSONResponse(
      status_code=422,
      content={
         "detail": {
            "type": "invalid_route_request",
            "entity_name": exception.entity_name,
            "msg": exception.msg
         }
      }
   )


# maybe make this a 404?
@app.exception_handler(PermissionsException)
def handle_permissions(
   _request: Request,
   exception: PermissionsException,
) -> JSONResponse:
   return JSONResponse(
      status_code=403,
      content={
         "detail": {
            "type": "forbidden"
         }
      }
   )


@app.exception_handler(DuplicateEntitiyException)
def handle_duplicates(
   _request: Request,
   exception: DuplicateEntitiyException
) -> JSONResponse:
   return JSONResponse(
      status_code=409,
      content={
         "detail": {
            "type": "duplicate_entity",
            "entity_name": exception.entity_name,
            "entity_id": exception.entity_id,
         }
      }
   )


lambda_handler = Mangum(app)

# from mangum import Mangum
# from fastapi import FastAPI 

# app = FastAPI()

# @app.get("/")
# def read_root():
#     return {"Hello, world!"}

# lambda_handler = Mangum(app)
