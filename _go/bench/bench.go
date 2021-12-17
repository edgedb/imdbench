package bench

import (
	"time"

	"github.com/edgedb/webapp-bench/_go/cli"
)

type Exec func(string, string) (time.Duration, string)
type Close func()
type Worker func(args cli.Args) (Exec, Close)
