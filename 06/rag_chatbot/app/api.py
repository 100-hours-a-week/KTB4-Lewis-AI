from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from app.pipeline import answer, answer_stream

app = FastAPI(title="KTB 부트캠프 규칙 챗봇")


class QueryRequest(BaseModel):
    question: str


@app.post("/query")
def query_endpoint(req: QueryRequest):
    text, contexts = answer(req.question)
    return {"answer": text, "contexts": contexts}


@app.post("/query/stream")
def query_stream_endpoint(req: QueryRequest):
    return StreamingResponse(answer_stream(req.question), media_type="text/event-stream")
