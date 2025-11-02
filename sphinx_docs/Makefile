# Makefile for Sphinx documentation

SPHINXBUILD   = sphinx-build
SOURCEDIR     = .
BUILDDIR      = _build

help:
	@echo "Please use 'make <target>' where <target> is one of"
	@echo "  html       to make standalone HTML files"
	@echo "  clean      to remove build artifacts"
	@echo "  livehtml   to start auto-rebuilding server"

html:
	$(SPHINXBUILD) -b html $(SOURCEDIR) $(BUILDDIR)/html
	@echo
	@echo "Build finished. The HTML pages are in $(BUILDDIR)/html."
	@echo "Open $(BUILDDIR)/html/index.html to view."

clean:
	rm -rf $(BUILDDIR)

livehtml:
	sphinx-autobuild -b html $(SOURCEDIR) $(BUILDDIR)/html

.PHONY: help html clean livehtml

