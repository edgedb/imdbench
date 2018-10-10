-- just add the benchmarks directy to the path
package.path = package.path .. ';./benchmarks/?.lua'
local bench_stats = require "bench_stats"
local bench_base = require "bench_base"


setup = bench_stats.setup
response = bench_stats.response
done = bench_stats.done
init = bench_base.pages.init
request = bench_base.pages.request
