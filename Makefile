SHELL := /bin/bash

start:
	ollama serve & source venv/bin/activate && python3 main.py

diovan:
	source venv/bin/activate && python3 diovan.py

stop:
	pkill ollama
