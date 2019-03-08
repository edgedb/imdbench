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
    wrk.thread:set('bench', args[3])
    print(string.format('INIT %s ids', name), #bench_base.ids[name])
end


function bench_base.single.request()
    if bench == 'gql' then
        -- we handle the query and variables parameters right here for GQL
        return wrk.format(
            'GET',
            wrk.path ..
            '&query=query+user%28%24uuid%3A+ID%29+%7B+UserDetails%28+filter%3A+%7Bid%3A+%7Beq%3A+%24uuid%7D%7D+%29+%7B+id+name+image+latest_reviews%28+order%3A+%7Bcreation_time%3A+%7Bdir%3A+DESC%7D%7D%2C+first%3A+3+%29+%7B+id+body+rating+movie+%7B+id+image+title+avg_rating+%7D+%7D+%7D+%7D+query+person%28%24uuid%3A+ID%29+%7B+PersonDetails%28+filter%3A+%7Bid%3A+%7Beq%3A+%24uuid%7D%7D+%29+%7B+id+full_name+image+bio+acted_in%28+order%3A+%7B+year%3A+%7Bdir%3A+ASC%7D%2C+title%3A+%7Bdir%3A+ASC%7D%2C+%7D+%29+%7B+id+image+title+year+avg_rating+%7D+directed+%28+order%3A+%7B+year%3A+%7Bdir%3A+ASC%7D%2C+title%3A+%7Bdir%3A+ASC%7D%2C+%7D+%29+%7B+id+image+title+year+avg_rating+%7D+%7D+%7D+query+movie%28%24uuid%3A+ID%29+%7B+MovieDetails%28+filter%3A+%7Bid%3A+%7Beq%3A+%24uuid%7D%7D+%29+%7B+id+image+title+year+description+directors%28+order%3A+%7B%7D+%29+%7B+id+full_name+image+%7D+cast+%7B+id+full_name+image+%7D+avg_rating+reviews%28+order%3A+%7Bcreation_time%3A+%7Bdir%3A+DESC%7D%7D%2C+%29+%7B+id+body+rating+author+%7B+id+name+image+%7D+%7D+%7D+%7D' ..
            '&variables=%7B%22uuid%22%3A%22' .. ids[math.random(#ids)] .. '%22%7D'
        )
    else
        return wrk.format('GET', wrk.path:format(ids[math.random(#ids)]))
    end
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
