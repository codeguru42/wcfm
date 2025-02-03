FROM python:3.13-slim

LABEL authors="codeguru"

ARG API_KEY
ARG AOC_SESSION_TOKEN

ENV API_KEY=${API_KEY}
ENV AOC_SESSION_TOKEN=${AOC_SESSION_TOKEN}

RUN pip install uv

WORKDIR /aoc
RUN uv init && uv add typer numpy pytest 

WORKDIR /app
COPY pyproject.toml .
RUN uv sync
COPY . .

CMD ["sh", "-c", "uv run solve_aoc.py $API_KEY /aoc/.venv/bin/python /aoc $AOC_SESSION_TOKEN"]