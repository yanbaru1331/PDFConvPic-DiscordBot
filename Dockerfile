FROM python:3.11

# 定義するもの
ENV PATH="/root/.local/bin:$PATH" 
ENV POETRY_HOME=/opt/poetry
WORKDIR /RePdf

#実行するもの
RUN wget -O - https://install.python-poetry.org | python3 - \
    && cd /usr/local/bin \
    && ln -s /opt/poetry/bin/poetry \
    && poetry config virtualenvs.create false \
    && apt update \
    && apt install poppler-utils poppler-data -y \
    && apt install tesseract-ocr libtesseract-dev poppler-utils tesseract-ocr-jpn -y \