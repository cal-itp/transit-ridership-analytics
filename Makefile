add_precommit:
	pip install pre-commit
	pre-commit install
	#pre-commit run --all-files

install_env:
	pip install uv && uv sync --all-groups
	make add_precommit

# installing venv takes up disk space in JupyterHub, about the same size as data-analyses and data-infra for a small repo!
#https://stackoverflow.com/questions/79154674/how-to-migrate-from-a-simple-python-project-requirements-txt-setup-py-setupto
uv_setup_project:
	pip install uv
	uv init
	#uv add package1 # go through and add packages, these are defined in pyproject.toml
	uv add _ridership_utils/
	uv lock
