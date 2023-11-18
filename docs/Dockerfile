FROM squidfunk/mkdocs-material

RUN pip install --no-cache-dir \
  mkdocstrings[python] \
  git+https://github.com/signalkraft/myPyllant.git

WORKDIR /build

COPY . .