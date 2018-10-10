-- just add the benchmarks directy to the path
package.path = package.path .. ';./benchmarks/?.lua'
local bench_base = require "bench_base"


init = bench_base.pages.init_sequential
request = bench_base.pages.request_sequential
