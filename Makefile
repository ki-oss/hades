lint:
	isort .
	pycln hades/ examples/ tests/ -a
	black --preview .
	blacken-docs -l 120 **/*.md
	mypy
	lint-imports
	
ci-lint:
	isort . --check --diff 
	pycln hades/ examples/ tests/ --check --diff -a
	black --preview --check .
	mypy
	blacken-docs -l 120 **/*.md
	lint-imports


coverage:
	coverage run -m pytest tests/
	coverage report --fail-under=100 -m


serve-docs:
	mkdocs serve --livereload
