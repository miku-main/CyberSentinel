# quality: lint, test, run
.PHONY: setup lint test run-app demo-data

setup:
	python3 -m venv .venv; \
	. .venv/bin/activate; \
	pip install --upgrade pip; \
	pip install -r requirements.txt

lint:
	. .venv/bin/activate; ruff check .

test:
	. .venv/bin/activate; \
	pytest -q; \
	code=$$?; \
	if [ $$code -eq 5 ]; then \
	echo "No tests collected (ok for Day 1)"; \
	exit 0; \
	else \
	exit $$code; \
	fi

run-app:
	. .venv/bin/activate; streamlit run app/ui/dashboard.py

demo-data:
	. .venv/bin/activate; python scripts/make_demo_data.py