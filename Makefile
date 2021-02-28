test: mypy pylint pytest pylint-strict
	echo "Nothing more to do"

mypy:
	mypy ghostmanager

pytest:
	python -m pytest --cov=ghostmanager --cov-report html --cov-report term

pylint:
	pylint ghostmanager --disable=R,C,W

pylint-strict:
	pylint ghostmanager --disable=R,C
