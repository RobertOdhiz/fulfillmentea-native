import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.models import OAuthFlows as OAuthFlowsModel, SecuritySchemeType
from fastapi.security import OAuth2

from .core.config import settings
from .db import Base, engine
from .models import *  # noqa

from .routers import auth, staff, riders, parcels, dispatch, delivery, payments, finance, inventory, sms


class OAuth2PasswordBearerWithCookie(OAuth2):
    def __init__(self, tokenUrl: str):
        flows = OAuthFlowsModel(password={"tokenUrl": tokenUrl})
        super().__init__(flows=flows, scheme_name="OAuth2PasswordBearer")


app = FastAPI(title="Fulfillmentea API", version="0.2.0",
              openapi_tags=[{"name": "auth"}],
              )

# Health check endpoint
@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "FulfillmentEA Backend"}

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup():
    os.makedirs(settings.media_dir, exist_ok=True)
    Base.metadata.create_all(bind=engine)


app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(staff.router, prefix="/staff", tags=["staff"])
app.include_router(riders.router, prefix="/riders", tags=["riders"])
app.include_router(parcels.router, prefix="/parcels", tags=["parcels"])
app.include_router(dispatch.router, prefix="/dispatch", tags=["dispatch"])
app.include_router(delivery.router, prefix="/delivery", tags=["delivery"])
app.include_router(payments.router, prefix="/payments", tags=["payments"])
app.include_router(finance.router, prefix="/finance", tags=["finance"])
app.include_router(inventory.router, prefix="/inventory", tags=["inventory"])
app.include_router(sms.router, prefix="/sms", tags=["sms"])


# Add global security scheme for Bearer token in Swagger UI
from fastapi.openapi.utils import get_openapi  # noqa

def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        routes=app.routes,
    )
    openapi_schema["components"] = openapi_schema.get("components", {})
    openapi_schema["components"]["securitySchemes"] = {
        "BearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT"
        }
    }
    openapi_schema["security"] = [{"BearerAuth": []}]
    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi
