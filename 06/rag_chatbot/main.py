import gradio as gr

from app.api import app
from ui.gradio_app import demo

app = gr.mount_gradio_app(app, demo, path="/")

# 실행: uvicorn main:app --reload
# - 채팅 UI: http://localhost:8000/
# - REST API: POST http://localhost:8000/query, /query/stream
