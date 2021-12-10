PROJECT=langstroth
REPO=registry.rc.nectar.org.au/nectar

DESCRIBE=$(shell git describe --tags --always)
IMAGE_TAG := $(if $(TAG),$(TAG),$(DESCRIBE))
IMAGE=$(REPO)/$(PROJECT):$(IMAGE_TAG)
LATEST=$(REPO)/$(PROJECT):latest
BUILDER=docker
BUILDER_ARGS=

build:
	echo "Derived image tag: $(DESCRIBE)"
	echo "Actual image tag: $(IMAGE_TAG)"
	$(BUILDER) build -f docker/Dockerfile $(BUILDER_ARGS) -t $(IMAGE) .
	$(BUILDER) tag $(IMAGE) $(LATEST)
push:
	$(BUILDER) push $(IMAGE)
	$(BUILDER) push $(LATEST)

.PHONY: build push
