.PHONY: clean


gobench: clean build main.go
	rm -rf "$(CURDIR)/_go"

build:
	GOPATH="$(CURDIR)/_go" go build -o gobench github.com/edgedb/webapp-bench/_go

clean:
	rm -f "$(CURDIR)/gobench"
	rm -rf "$(CURDIR)/_go"
