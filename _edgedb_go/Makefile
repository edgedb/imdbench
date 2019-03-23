.PHONY: clean


bench: main.go
	# rm -rf "$(CURDIR)/_go" && mkdir "$(CURDIR)/_go"
	# GOPATH="$(CURDIR)/_go" go get gopkg.in/alecthomas/kingpin.v2 \
	# 							  github.com/valyala/fasthttp
	# mkdir -p "$(CURDIR)/_go/src/github.com/edgedb/bench/"
	# ln -s "$(CURDIR)" "$(CURDIR)/_go/src/github.com/edgedb/bench/_golang"
	GOPATH="$(CURDIR)/_go" go build -o gobench github.com/edgedb/bench/_golang
	# rm -rf "$(CURDIR)/_go"

clean:
	rm -f "$(CURDIR)/pgbench_golang"
	rm -rf "$(CURDIR)/_go"
