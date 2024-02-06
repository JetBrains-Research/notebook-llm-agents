import io
import pdb
import sys

from fastapi import FastAPI, HTTPException, Request


class CustomDebugger(pdb.Pdb):
    def __init__(self):
        super().__init__()
        self.stdout = sys.stdout
        sys.stdout = self.trace_output = io.StringIO()

    def get_trace_output(self):
        sys.stdout = self.stdout
        return self.trace_output.getvalue()


db = {}

Server_B = FastAPI()


@Server_B.post("/execute_code/")
async def execute_code(request: Request):
    form_data = await request.form()
    code = form_data.get("code")
    debugger = CustomDebugger()
    exec_locals = {}
    try:
        debugger.runcall(exec, code, db, exec_locals)
        output = exec_locals
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        trace_output = debugger.get_trace_output()
    return {"output": output, "trace_output": trace_output}


@Server_B.get("/get_variables/")
async def get_variables():
    return db
