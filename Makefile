coverage:
	coverage run -m pytest
	coverage html --omit="test_*.py"
	coverage xml --omit="test_*.py"
	open htmlcov/index.html || true

check-coverage:
	coverage run -m pytest
	coverage xml --omit="test_*.py"
	coverage report --fail-under=80

install:
	pip install -r requirements.txt

lint:
	flake8 --exclude=venv/,terraform/ --max-line-length=130 .

freeze:
	pip freeze > requirements.txt

test:
	python3 -m pytest -rP .

run:
	source env.sh ; python3 main.py