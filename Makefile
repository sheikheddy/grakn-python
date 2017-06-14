init:
	pip install pipenv
	pipenv install --dev

test:
	pipenv run nosetests

accept:
	pipenv run behave --tags=-skip