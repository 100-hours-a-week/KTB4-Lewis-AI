# 카카오 테크 부트캠프 규칙 챗봇 (RAG)

Gemini API + Chroma + Gradio로 구현한, 부트캠프 운영 규칙(출결/공결 신청 등)을 답변하는 RAG 챗봇.

## 구조

```
app/
├── ingestion/    # 마크다운 문서 로딩 + 헤더 기반 청킹
├── retrieval/    # Gemini 임베딩 + Chroma 벡터 검색
├── generation/   # Gemini 채팅 모델 호출 (동기/스트리밍)
├── pipeline.py   # ingest_all / answer / answer_stream
└── api.py        # FastAPI: POST /query, /query/stream
ui/
└── gradio_app.py # gr.ChatInterface 기반 채팅 UI
eval/
├── dataset.py      # 평가용 질문-정답 셋
└── ragas_eval.py   # RAGAS 평가 (faithfulness, answer_relevancy, context_precision/recall)
data/
└── ktb_rules.md  # 실제 부트캠프 규칙을 채워야 하는 문서
main.py           # FastAPI에 Gradio UI를 마운트하는 엔트리포인트
ingest.py         # data/ 문서를 Chroma에 적재하는 스크립트
```

## 실행 방법

```bash
pip install -r requirements.txt
cp .env.example .env   # GEMINI_API_KEY 채우기

# 1. data/ktb_rules.md를 실제 규칙으로 채운 뒤 적재
python ingest.py

# 2. 서버 실행 (UI: http://localhost:8000/, API: /query, /query/stream)
uvicorn main:app --reload
```
## 대회내용 예시
user: 안녕

assistant: 안녕하세요! 카카오 테크 부트캠프 운영 규칙에 대해 궁금한 점이 있으시면 언제든지 질문해주세요.

user: 오늘 아파서 그런데 수업 빠지고 싶어 어떻게 해야해

assistant: 안녕하세요! 카카오 테크 부트캠프 챗봇 헬퍼 라이언입니다. 오늘 몸이 아프셔서 수업에 참여하기 어려우시군요.

당일 급성 통증으로 인한 질병 결석은 다음과 같이 처리하시면 됩니다.

1.  **즉시 헬퍼 라이언에게 연락:** 가장 먼저 **DM** 또는 **유선(031-600-8502)**으로 헬퍼 라이언에게 오늘 아파서 수업에 참여하기 어렵다는 사실을 공유해주세요.
2.  **병원 방문:** 병원에 방문하여 진료를 받으세요.
3.  **증빙 서류 제출:** 당일 병원 방문 후, **오후 5시 전까지 통합신청센터에 증빙 서류**를 제출해주셔야 합니다.
    *   진단서 비용이 부담될 경우, **진료확인서**로 대체 가능합니다.
    *   대학병원 방문 시에는 **처방전**으로 대체 가능합니다.
4.  **사전신청 후 사후신청 필수:** 일반적으로는 사유 발생 최소 3일 전(평일 기준) 사전 신청이 원칙이지만, 당일 급성 통증의 경우 위의 절차를 따르며, 이후에 **사후신청** 절차를 완료해주셔야 합니다.

**유의사항:**

*   미용 목적(치과/피부과 시술 등)이나 검사 결과 확인 목적(정기검진/이미 진료받은 내역)은 출석 인정 사유에서 제외됩니다.
*   공가(질병) 사용은 전체 소정 훈련 일수의 10%까지만 가능하며, 잦은 질병 신청 시 헬퍼 라이언과 면담이 진행될 수 있습니다.

혹시 더 궁금한 점이 있으시면 디스코드 출석문의사항 채널에 문의해주세요. 얼른 쾌차하시길 바랍니다!

user: 부트캠프 쉬는날 언제야?

assistant: 카카오 테크 부트캠프의 쉬는 날은 다음과 같습니다.

**휴강 및 공휴일:**
*   5월 25일(월): 부처님오신날 대체공휴일
*   6월 3일(수): 지방선거
*   6월 26일(금): 휴강
*   7월 17일(금): 휴강
*   8월 13일(목) ~ 8월 14일(금): 휴강
*   8월 17일(월): 광복절 대체공휴일
*   9월 24일(목) ~ 9월 25일(금): 추석 연휴
*   10월 5일(월): 개천절 대체공휴일
*   10월 9일(금): 한글날

**특별 일정:**
*   **AI 주간:**
    *   부하테스트: 8월 10일(월) ~ 8월 12일(수) (2박 3일)
    *   AI 해커톤: 8월 18일(화) ~ 8월 21일(금) (3박 4일)
*   **오프라인 네트워킹:**
    *   1차: 7월 16일(목)
    *   2차: 9월 18일(금)

이 외에 개인적인 사유로 인한 휴가는 `휴가 신청 절차`에 따라 사전 신청 후 사용하실 수 있습니다.

## 평가

```bash
python -m eval.ragas_eval
```

`eval/dataset.py`의 `ground_truth`를 `data/ktb_rules.md` 내용에 맞게 채운 뒤 실행한다.

## 참고

- 문서가 추가/수정되면 `python ingest.py`를 다시 실행해 Chroma 컬렉션을 갱신한다 (같은 `source`+`heading`+순번 id는 upsert되어 중복되지 않는다).

