.PHONY: clean docs

default: clean docs

clean:
	rm -rf ./docs

docs:
	pydoctor \
		--project-name=houclip \
		--project-version=0.5 \
		--make-html \
		--html-output=docs/api \
		--docformat=google \
		--intersphinx=https://docs.python.org/3/objects.inv \
		--project-base-dir="." \
		./scripts/python/houclip
