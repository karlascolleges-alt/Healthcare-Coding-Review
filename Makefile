.PHONY: install run test quality dashboard api

install:
	python -m pip install -e ".[app,dev]"

run:
	coding-review

test:
	python -m pytest

quality:
	python -m ruff check .
	python -m sqlfluff lint --dialect snowflake sql

dashboard:
	streamlit run app/dashboard.py

api:
	uvicorn app.api:app --reload

