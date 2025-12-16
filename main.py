import argparse
import os
import spacy
from pathlib import Path
from typing import Dict, Any
from dotenv import load_dotenv
from openai import OpenAI
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from rouge_score import rouge_scorer
from collections import Counter

nlp = spacy.load("ru_core_news_sm")

load_dotenv()

MODELS = {
    "model_a": "x-ai/grok-code-fast-1",
    "model_b": "google/gemini-2.0-flash-001",
    "judge": "meta-llama/llama-3.3-70b-instruct",
}

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv("API_KEY"),
)


class TextAnalyzer:
    @staticmethod
    def get_spacy_stats(text: str) -> dict[str, Any]:
        doc = nlp(text)

        pos_counts = Counter()
        token_count = 0
        sentence_count = 0

        for token in doc:
            if not token.is_space and not token.is_punct:
                pos_counts[token.pos_] += 1
                token_count += 1

        sentence_count = sum(1 for _ in doc.sents)

        avg_sent_len = token_count / sentence_count if sentence_count > 0 else 0

        return {
            "token_count": token_count,
            "sentence_count": sentence_count,
            "avg_sentence_length": round(avg_sent_len, 2),
            "pos_distribution": dict(pos_counts),
        }

    @staticmethod
    def calculate_cosine_similarity(text1: str, text2: str) -> float:
        if not text1 or not text2:
            return 0.0

        vectorizer = TfidfVectorizer().fit_transform([text1, text2])
        vectors = vectorizer.toarray()
        return float(cosine_similarity(vectors)[0][1])

    @staticmethod
    def calculate_rouge(reference: str, candidate: str) -> Dict[str, float]:
        scorer = rouge_scorer.RougeScorer(["rougeL"], use_stemmer=True)
        scores = scorer.score(reference, candidate)
        return {
            "rougeL_fmeasure": round(scores["rougeL"].fmeasure, 4),
            "rougeL_precision": round(scores["rougeL"].precision, 4),
            "rougeL_recall": round(scores["rougeL"].recall, 4),
        }


def generate_summary(text: str, model: str) -> str:
    completion = client.chat.completions.create(
        extra_body={},
        model=model,
        messages=[
            {
                "role": "user",
                "content": f"Создай подробный реферат на русском языке для следующего текста. Сохраняй структуру и ключевые факты:\n\n{text}",
            }
        ],
    )
    return completion.choices[0].message.content


def run_judge(
    original: str, summary_a: str, summary_b: str, model_a_name: str, model_b_name: str
) -> str:
    prompt = f"""
    Ты - эксперт-лингвист и редактор. Твоя задача - сравнить два реферата (summary) одного и того же исходного текста.
    
    Исходный текст (начало):
    {original}...
    
    Реферат от модели {model_a_name}:
    {summary_a}
    
    Реферат от модели {model_b_name}:
    {summary_b}
    
    Проведи анализ по следующим пунктам:
    1. Точность передачи смысла (оценка 1-10 для каждого).
    2. Фактические ошибки или галлюцинации (есть ли они?).
    3. Читаемость и структура (какой текст лучше структурирован?).
    4. Итоговое резюме: какой реферат лучше и почему?
    
    Ответ дай в формате Markdown.
    """

    completion = client.chat.completions.create(
        extra_body={},
        model=MODELS["judge"],
        messages=[{"role": "user", "content": prompt}],
    )
    return completion.choices[0].message.content


def main():
    parser = argparse.ArgumentParser(description="LLM Summary Comparator & Evaluator")
    parser.add_argument("filename", type=Path, help="Path to source file")
    args = parser.parse_args()

    file_path = args.filename
    if not file_path.exists():
        print(f"File not found: {file_path}")
        return

    print(f"Reading {file_path}...")
    with open(file_path, "r", encoding="utf-8") as f:
        original_text = f.read()

    print(f"Generating summary with {MODELS['model_a']}...")
    summary_a = generate_summary(original_text, MODELS["model_a"])

    print(f"Generating summary with {MODELS['model_b']}...")
    summary_b = generate_summary(original_text, MODELS["model_b"])

    print("Calculating metrics...")
    stats_a = TextAnalyzer.get_spacy_stats(summary_a)
    stats_b = TextAnalyzer.get_spacy_stats(summary_b)

    # Cosine Similarity (Summary vs Original) - approximating semantic retention
    sim_a_orig = TextAnalyzer.calculate_cosine_similarity(original_text, summary_a)
    sim_b_orig = TextAnalyzer.calculate_cosine_similarity(original_text, summary_b)

    # Inter-Model Agreement (ROUGE & Cosine between summaries)
    rouge_ab = TextAnalyzer.calculate_rouge(summary_a, summary_b)
    sim_ab = TextAnalyzer.calculate_cosine_similarity(summary_a, summary_b)

    # 3. Qualitative Analysis (LLM Judge)
    print("Asking the Judge...")
    judge_verdict = run_judge(
        original_text, summary_a, summary_b, MODELS["model_a"], MODELS["model_b"]
    )

    report = f"""# Отчет о сравнении моделей реферирования

**Исходный файл:** {file_path.name}
**Длина оригинала:** {len(original_text)} символов

---

## 1. Количественные показатели

| Метрика | {MODELS["model_a"]} | {MODELS["model_b"]} |
|---------|---------------------|---------------------|
| Длина (символов) | {len(summary_a)} | {len(summary_b)} |
| Длина (токенов/слов) | {stats_a["token_count"]} | {stats_b["token_count"]} |
| Предложений | {stats_a["sentence_count"]} | {stats_b["sentence_count"]} |
| Ср. длина предложения | {stats_a["avg_sentence_length"]} | {stats_b["avg_sentence_length"]} |
| Сходство с оригиналом (Cosine TF-IDF) | {sim_a_orig:.4f} | {sim_b_orig:.4f} |

### Анализ частей речи (структурность)
* **Model A:** {stats_a["pos_distribution"]}
* **Model B:** {stats_b["pos_distribution"]}

---

## 2. Сравнение моделей между собой (Inter-Agreement)
*Насколько модели согласны друг с другом?*

* **Косинусное сходство (A vs B):** {sim_ab:.4f}
* **ROUGE-L (A vs B):** F-measure: {rouge_ab["rougeL_fmeasure"]} (Precision: {rouge_ab["rougeL_precision"]}, Recall: {rouge_ab["rougeL_recall"]})

---

## 3. Вердикт AI-судьи ({MODELS["judge"]})

{judge_verdict}

---

## Приложения: Тексты рефератов

### Реферат {MODELS["model_a"]}
{summary_a}

### Реферат {MODELS["model_b"]}
{summary_b}
"""

    output_path = file_path.parent / "comparison_report_{file_path.stem}.md"
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(report)

    print(f"\nReport saved to: {output_path}")


if __name__ == "__main__":
    main()
