import gradio as gr

from app.pipeline import answer_stream


def chat_fn(message: str, history: list[dict]) -> str:
    partial = ""
    for token in answer_stream(message):
        partial += token
        yield partial


demo = gr.ChatInterface(
    fn=chat_fn,
    title="카카오 테크 부트캠프 규칙 챗봇",
    description="출결, 공결 신청 등 부트캠프 운영 규칙에 대해 물어보세요.",
)
