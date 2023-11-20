FROM squidfunk/mkdocs-material

RUN pip install --no-cache-dir \
  mkdocs-material[imaging] \
  mkdocstrings[python] \
  git+https://github.com/signalkraft/myPyllant.git

WORKDIR /docs

COPY .git .
COPY docs/ .