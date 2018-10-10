local bench_stats = {
    threads = {}
}


function bench_stats.get_stats(t)
    local raw = {}
    local min, mean, m50, m75, m90, m99, max, sum, vm, sumvm2
    sum = 0

    -- copy the values so that can be sorted without altering the original
    for k, v in ipairs(t) do raw[k] = v end

    table.sort(raw)

    min = raw[1]
    max = raw[#raw]
    m50 = raw[math.ceil(#raw * 0.5)]
    m75 = raw[math.ceil(#raw * 0.75)]
    m90 = raw[math.ceil(#raw * 0.9)]
    m99 = raw[math.ceil(#raw * 0.99)]

    for _, v in pairs(raw) do
        sum = sum + v
    end

    mean = sum / #raw

    -- sum of vm^2
    sumvm2 = 0
    for _, v in pairs(raw) do
        vm = v - mean
        sumvm2 = sumvm2 + vm ^ 2
    end
    stdev = math.sqrt(sumvm2 / (#raw - 1))

    return {
        raw=raw,
        min=min, mean=mean, max=max, sum=sum, stdev=stdev,
        ['50%']=m50, ['75%']=m75, ['90%']=m90, ['99%']=m99
    }
end


function bench_stats.setup(thread)
    table.insert(bench_stats.threads, thread)
    thread:set('queries', {})
    thread:set('time_ms', {})
end


function bench_stats.response(status, headers, body)
    local chunk = body:sub(0, 100)
    local _, _, q, t = body:find(
        '"queries":%s*(%d+),%s*"time_ms":%s*(%d+%.?%d*)')

    table.insert(queries, tonumber(q))
    table.insert(time_ms, tonumber(t))
end


function bench_stats.done(summary, latency, requests)
    local header = '\t\tmin\tmean\tmax\tstdev\t50%\t75%\t90%\t99%'
    local stats = {}
    print(header)
    for _, thread in pairs(bench_stats.threads) do
        for _, name in ipairs({'queries', 'time_ms'}) do
            local vals = thread:get(name)
            stats[name] = bench_stats.get_stats(vals)

            local line = name .. '\t\t'
            for _, col in ipairs({
                    'min', 'mean', 'max', 'stdev',
                    '50%', '75%', '90%', '99%'
                })
            do
                if col == 'mean' or col == 'stdev' then
                    line = line .. string.format('%.2f\t', stats[name][col])
                else
                    line = line .. string.format('%d\t', stats[name][col])
                end
            end
            print(line)
        end

        -- add on the latency data
        line = 'latency\t\t'
        local lat
        for _, col in ipairs({
                'min', 'mean', 'max', 'stdev',
                50, 75, 90, 99
            })
        do
            if type(col) == 'number' then
                lat = latency:percentile(col) / 1000
            else
                lat = latency[col] / 1000
            end

            line = line .. string.format('%.2f\t', lat)
        end
        print(line)
    end
end

return bench_stats
