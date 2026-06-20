"""RAGAS로 RAG 파이프라인을 평가한다.

실행 전 ingest.py로 Chroma에 문서를 적재하고, eval/dataset.py의 ground_truth를 채워야 한다.
실행: python -m eval.ragas_eval
"""

from datasets import Dataset
from ragas import evaluate
from ragas.metrics import answer_relevancy, context_precision, context_recall, faithfulness

from app.pipeline import answer
from eval.dataset import EVAL_QUESTIONS


def build_eval_dataset() -> Dataset:
    questions, answers, contexts_list, ground_truths = [], [], [], []

    for item in EVAL_QUESTIONS:
        generated_answer, contexts = answer(item["question"])
        questions.append(item["question"])
        answers.append(generated_answer)
        contexts_list.append([c["text"] for c in contexts])
        ground_truths.append(item["ground_truth"])

    return Dataset.from_dict(
        {
            "question": questions,
            "answer": answers,
            "contexts": contexts_list,
            "ground_truth": ground_truths,
        }
    )


if __name__ == "__main__":
    dataset = build_eval_dataset()
    result = evaluate(
        dataset,
        metrics=[faithfulness, answer_relevancy, context_precision, context_recall],
    )
    print(result)
