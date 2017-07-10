init:
	pip install pipenv
	pipenv install --dev

test:
	pipenv run nosetests

accept:
	pipenv run behave features/grakn-spec/features --tags=-skip -D graknversion=$(GRAKNVERSION)