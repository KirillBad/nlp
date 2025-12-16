import argparse
import re
import spacy
from pathlib import Path
from collections import Counter
from typing import Generator
import matplotlib.pyplot as plt
from wordcloud import WordCloud

nlp = spacy.load("ru_core_news_sm")


def normalize(text: str) -> str:
    return re.sub(r"[^a-zа-яё\s]", " ", text.lower())


def process_text_spacy(text: str, stop_words: set[str]) -> Generator[str, None, None]:
    doc = nlp(text)

    for token in doc:
        if not token.is_space and token.lemma_ not in stop_words:
            yield token.lemma_


def create_visualizations(counter: Counter, title_name: str, output_dir: Path) -> None:
    top_20 = counter.most_common(20)

    words = [item[0] for item in top_20]
    counts = [item[1] for item in top_20]

    plt.figure(figsize=(12, 8))
    plt.barh(words[::-1], counts[::-1], color="skyblue")
    plt.xlabel("Frequency")
    plt.title(f"Top 20 Lemmas: {title_name}")
    plt.tight_layout()

    bar_path = output_dir / f"barchart_{title_name}.png"
    plt.savefig(bar_path)
    plt.close()

    wordcloud = WordCloud(
        width=1600, height=800, background_color="white", colormap="viridis"
    ).generate_from_frequencies(counter)

    plt.figure(figsize=(20, 10))
    plt.imshow(wordcloud, interpolation="bilinear")
    plt.axis("off")

    wc_path = output_dir / f"wordcloud_{title_name}.png"
    plt.savefig(wc_path)
    plt.close()


def main():
    parser = argparse.ArgumentParser(description="Batch NLP Pipeline.")

    parser.add_argument("filenames", type=Path, nargs="+", help="Paths to source files")
    parser.add_argument(
        "-s", "--stopwords", nargs="*", default=[], help="List of stop words"
    )

    args = parser.parse_args()
    stop_words = set(args.stopwords)

    global_counter = Counter()

    first_file = args.filenames[0]
    if not first_file.exists():
        print(f"Error: First file {first_file} not found.")
        return

    output_dir = first_file.parent

    print(f"Starting batch processing of {len(args.filenames)} files...\n")

    for file_path in args.filenames:
        if not file_path.exists():
            print(f"Skipping missing file: {file_path}")
            continue

        print(f"Processing: {file_path.name}...")

        with open(file_path, "r", encoding="utf-8") as f:
            normalized_content = normalize(f.read())

        current_file_lemmas = []

        for lemma in process_text_spacy(normalized_content, stop_words):
            current_file_lemmas.append(lemma)
            global_counter[lemma] += 1

        output_txt_path = output_dir / f"processed_{file_path.name}"
        with open(output_txt_path, "w", encoding="utf-8") as f:
            f.write(", ".join(current_file_lemmas))

    if len(args.filenames) == 1:
        result_name = args.filenames[0].stem
    else:
        result_name = "combined_corpus"

    create_visualizations(global_counter, result_name, output_dir)

    print("\nTop 20 Global Lemmas:")
    print("-" * 30)
    for lemma, count in global_counter.most_common(20):
        print(f"{lemma:<20} | {count}")
    print("-" * 30)


if __name__ == "__main__":
    main()
