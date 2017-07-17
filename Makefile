all: env binary packages doc test
all-docker: env-docker binary-docker packages-docker doc-docker test-docker

clean:
	@bash scripts/clean.sh

distclean: clean
	@bash scripts/distclean.sh

env:
	@bash scripts/env.sh

binary: env
	@bash scripts/binary.sh

packages: env
	@bash scripts/packages.sh

doc: env
	@bash scripts/doc.sh

test: env
	@bash scripts/test.sh

env-docker:
	@bash scripts/docker.sh env

binary-docker: env-docker
	@bash scripts/docker.sh binary

packages-docker: env-docker
	@bash scripts/docker.sh packages

doc-docker: env-docker
	@bash scripts/docker.sh doc

test-docker: env-docker
	@bash scripts/docker.sh test

.PHONY: env env-docker
