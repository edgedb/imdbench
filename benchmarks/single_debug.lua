-- just add the benchmarks directy to the path
package.path = package.path .. ';./benchmarks/?.lua'
local bench_stats = require "bench_stats"
local bench_base = require "bench_base"

local ids = {}


setup = bench_stats.setup
response = bench_stats.response
done = bench_stats.done
init = bench_base.single.init
request = bench_base.single.request
