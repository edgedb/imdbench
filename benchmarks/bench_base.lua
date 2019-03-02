local bench_base = {
    ids={},
    single={},
    pages={},
}


function bench_base.load_ids(name, t)
    -- if the ids have not been read from a file, load them
    if bench_base.ids[name] == nil then
        -- create a new table for ids
        bench_base.ids[name] = {}
        -- load them from the corresponding file
        for line in io.lines(string.format(
            'benchmarks/%s_ids_100000_100000_500000.txt', name))
        do
            if t == 'int' then
                table.insert(bench_base.ids[name], tonumber(line))
            else
                table.insert(bench_base.ids[name], line)
            end
        end
    end
end


function bench_base.single.init(args)
    local name = args[1]
    local t = 'int'

    if args[2] == 'edb' then
        name = 'edgedb_'..name
        t = 'str'
    end
    -- read the ids from a file, so that we can pick them randomly
    bench_base.load_ids(name, t)
    wrk.thread:set('ids', bench_base.ids[name])
    print(string.format('INIT %s ids', name), #bench_base.ids[name])
end


function bench_base.single.request()
    return wrk.format('GET', wrk.path:format(ids[math.random(#ids)]))
end


function bench_base.single.init_sequential(args)
    bench_base.single.init(args)
    wrk.thread:set('index', 0)
end


function bench_base.single.request_sequential()
    index = index + 1
    if index > #ids then index = 1 end
    return wrk.format('GET', wrk.path:format(ids[index]))
end


function bench_base.pages.init(args)
    local name = args[1]
    local t = 'int'

    if args[2] == 'edb' then
        name = 'edgedb_'..name
        t = 'str'
    end
    -- read the ids from a file, so that we can figure out page_count
    bench_base.load_ids(name)
    local pages = math.ceil(#bench_base.ids[name] / 10)
    wrk.thread:set('pages', pages)

    print(string.format('INIT %s pages', name), pages)
end


function bench_base.pages.request()
    return wrk.format('GET', wrk.path:format(math.random(pages) - 1))
end


function bench_base.pages.init_sequential(args)
    bench_base.pages.init(args)
    wrk.thread:set('index', 0)
end


function bench_base.pages.request_sequential()
    index = index + 1 % pages
    return wrk.format('GET', wrk.path:format(index))
end


return bench_base
