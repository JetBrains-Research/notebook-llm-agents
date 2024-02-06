import requests
from fastapi import FastAPI
from fastapi import Request, Form
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

Server_A = FastAPI()

templates = Jinja2Templates(directory="templates")


@Server_A.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@Server_A.post("/send_code/")
async def send_code(request: Request, code: str = Form(...)):
    url = "http://127.0.0.1:8001/execute_code"
    data = {"code": code}
    response = requests.post(url, data=data)
    output = response.text
    return templates.TemplateResponse(
        "output.html", {"request": request, "code": code, "output": output}
    )


@Server_A.get("/get_variables/")
async def get_variables():
    url = "http://127.0.0.1:8001/get_variables/"
    response = requests.get(url)
    return response.json()
