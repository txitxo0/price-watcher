from app.core.config import settings
from .base import BasePriceCRUD

price_crud_handler: BasePriceCRUD

if settings.DB_TYPE == "sqlite":
    from .sqlite_crud import SQLitePriceCRUD
    price_crud_handler = SQLitePriceCRUD(db_path=settings.DB_FILE)
# elif settings.DB_TYPE == "postgres":
#     from .postgres_crud import PostgresPriceCRUD # You would create this file
#     # Example: Construct DSN or pass individual params
#     pg_dsn = f"postgresql://{settings.DB_USER}:{settings.DB_PASSWORD}@{settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}"
#     price_crud_handler = PostgresPriceCRUD(dsn=pg_dsn)
# elif settings.DB_TYPE == "mongodb":
#     from .mongodb_crud import MongoDBPriceCRUD # You would create this file
#     # Example: Construct URI or pass individual params
#     mongo_uri = f"mongodb://{settings.DB_USER}:{settings.DB_PASSWORD}@{settings.DB_HOST}:{settings.DB_PORT}/"
#     price_crud_handler = MongoDBPriceCRUD(
#         uri=mongo_uri,
#         database_name=settings.DB_NAME
#     )
else:
    raise ValueError(f"Unsupported DB_TYPE: {settings.DB_TYPE} configured in .env or settings.")

# Now, other modules can import and use `price_crud_handler`