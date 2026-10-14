.PHONY: data analyze all clean

PYTHON ?= python3

data:
	$(PYTHON) -m src.download.download_all

analyze:
	$(PYTHON) -m src.analysis.run_analyses

all:
	$(PYTHON) run_all.py

clean:
	rm -f data/manifest.json data/SOURCES.md
	rm -rf data/processed/*.csv data/processed/*.json
	rm -f outputs/figures/*.png outputs/tables/*.csv
