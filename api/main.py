from fastapi import FastAPI
from api.routers import consulting, patent_search, claims, examiner, drawing, description

app = FastAPI(title="Patent Agent API")

app.include_router(consulting.router,     prefix="/consult",        tags=["Consulting"])
app.include_router(patent_search.router,  prefix="/patent-search",  tags=["Patent Search"])
app.include_router(claims.router,         prefix="/claims",         tags=["Claims"])
app.include_router(examiner.router,       prefix="/examine",        tags=["Examiner"])
app.include_router(drawing.router,        prefix="/drawing",        tags=["Drawing"])
app.include_router(description.router,    prefix="/description",    tags=["Description"])
