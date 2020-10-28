.PHONY: clean


gobench: develop build main.go
	rm -rf "$(CURDIR)/_go"

develop: clean
	mkdir -p "$(CURDIR)/_go/src/github.com/edgedb/edgedb-go"
	git clone git@github.com:edgedb/edgedb-go.git \
		"$(CURDIR)/_go/src/github.com/edgedb/edgedb-go"
	GOPATH="$(CURDIR)/_go" go get gopkg.in/alecthomas/kingpin.v2 \
								  github.com/valyala/fasthttp \
								  github.com/edgedb/edgedb-go/edgedb
	mkdir -p "$(CURDIR)/_go/src/github.com/edgedb/bench/"
	ln -s "$(CURDIR)" "$(CURDIR)/_go/src/github.com/edgedb/bench/_golang"

build:
	GOPATH="$(CURDIR)/_go" go build -o gobench github.com/edgedb/bench/_golang


clean:
	rm -f "$(CURDIR)/pgbench_golang"
	rm -rf "$(CURDIR)/_go"
