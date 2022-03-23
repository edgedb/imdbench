.PHONY: clean


gobench: clean build main.go
	test -d "$(CURDIR)/_go" && chmod -R u+w "$(CURDIR)/_go" || :
	rm -rf "$(CURDIR)/_go"

build:
	GOPATH="$(CURDIR)/_go" go build -o gobench github.com/edgedb/imdbench/_go

clean:
	rm -f "$(CURDIR)/gobench"
	test -d "$(CURDIR)/_go" && chmod -R u+w "$(CURDIR)/_go" || :
	rm -rf "$(CURDIR)/_go"
