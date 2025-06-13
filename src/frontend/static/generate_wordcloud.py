#!/usr/bin/env python3
"""
Generate a wordcloud from CIRED document themes.

This script creates a wordcloud visualization from document themes and saves it
as a static image that can be served by the analytics server.
"""

import logging
import re
from collections import Counter
from pathlib import Path

import matplotlib.pyplot as plt
from r2r import R2RClient
from wordcloud import STOPWORDS, WordCloud
from words import CIRED_THEMES, KEEP_INITIALIZED, MY_STOPWORDS, TRANSLATION_TABLE

from intake.config import R2R_DEFAULT_BASE_URL, setup_logging
from intake.utils import get_server_documents

setup_logging()


def get_titles_from_r2r() -> list[str]:
    """Fetch the list of document titles from the R2R server."""
    client = R2RClient(base_url=R2R_DEFAULT_BASE_URL)
    df = get_server_documents(client)
    if df is None or "title" not in df.columns:
        logging.error("Could not find publication titles from the R2R server")
        return []
    raw_titles = df["title"].dropna().astype(str).tolist()
    return raw_titles


def clean_titles(raw_titles: list[str]) -> list[str]:
    """Nettoie les titres : suppression de stopwords, mise en minuscules sauf exceptions, application du tableau de traduction."""
    cleaned_titles: list[str] = []
    for title in raw_titles:
        cleaned_words: list[str] = []
        parts = re.split(r"[ :\?']", title)
        for word in parts:
            key = word if word in KEEP_INITIALIZED else word.lower()
            if key in STOPWORDS or key in MY_STOPWORDS:
                continue
            mapped = TRANSLATION_TABLE.get(key, key)
            cleaned_words.append(mapped)
        cleaned_titles.append(" ".join(cleaned_words))

    # Enregistrer les vocabulaires brut et nettoyé avec leurs fréquences
    static_dir = Path(__file__).parent
    raw_counts = Counter(raw for title in raw_titles for raw in title.split())
    cleaned_counts = Counter(word for title in cleaned_titles for word in title.split())
    with open(static_dir / "wordbag-raw.txt", "w", encoding="utf-8") as f:
        for word, count in raw_counts.most_common():
            f.write(f"{count}\t{word}\n")
    with open(static_dir / "wordbag-processed.txt", "w", encoding="utf-8") as f:
        for word, count in cleaned_counts.most_common():
            f.write(f"{count}\t{word}\n")
    return cleaned_titles


def create_wordcloud(text: str, output_path: Path) -> None:
    """Create and save a wordcloud from the given text."""
    wordcloud = WordCloud(
        width=1024,
        height=640,
        background_color="white",
        max_words=100,
        stopwords=STOPWORDS.union(MY_STOPWORDS),
        colormap="viridis",
        relative_scaling=0.4,
        min_font_size=10,
        max_font_size=60,
        prefer_horizontal=0.7,
        collocations=True,
        scale=2,
    ).generate(text)

    plt.figure(figsize=(12.8, 8))
    plt.imshow(wordcloud, interpolation="bilinear")
    plt.axis("off")
    plt.tight_layout(pad=0)
    plt.savefig(
        output_path, dpi=80, bbox_inches="tight", facecolor="white", edgecolor="none"
    )
    plt.close()

    logging.info(f"Wordcloud saved to: {output_path}")


def main() -> None:
    """Generate the CIRED themes wordcloud."""
    output_path = Path("cired_wordcloud.png")

    raw_titles = get_titles_from_r2r()
    titles = clean_titles(raw_titles)
    if titles:
        text = " ".join(titles)
        logging.info(
            "Generating wordcloud from a bag of %d titles (%d words)",
            len(titles),
            len(text.split()),
        )
    else:
        logging.warning("Using hardcoded themes to generate wordcloud.")
        text = CIRED_THEMES

    create_wordcloud(text, output_path)


if __name__ == "__main__":
    main()
