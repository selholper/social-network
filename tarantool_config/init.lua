box.cfg {
    listen = 3301,
    memtx_memory = 128 * 1024 * 1024, -- 128MB
    checkpoint_interval = 60,
    checkpoint_count = 6,
    wal_mode = "write",
    log_level = 5,
    log = 'tarantool.log'
}

-- Создание пользователя для подключения
box.once("bootstrap", function()
    -- Создаем пользователя admin
    box.schema.user.create('tarantool', {password = 'tarantool', if_not_exists = true})
    box.schema.user.grant('tarantool', 'read,write,execute', 'universe', nil, {if_not_exists = true})
    
    -- Создание спейсов для социальной сети
    
    -- Спейс для пользовательских сессий
    local user_sessions = box.schema.space.create('user_sessions', {if_not_exists = true})
    user_sessions:format({
        {name = 'session_id', type = 'string'},
        {name = 'user_id', type = 'unsigned'},
        {name = 'data', type = 'map'},
        {name = 'expires_at', type = 'unsigned'}
    })
    user_sessions:create_index('primary', {
        parts = {'session_id'},
        type = 'HASH',
        unique = true,
        if_not_exists = true
    })
    user_sessions:create_index('user_id', {
        parts = {'user_id'},
        type = 'TREE',
        unique = false,
        if_not_exists = true
    })
    user_sessions:create_index('expires_at', {
        parts = {'expires_at'},
        type = 'TREE',
        unique = false,
        if_not_exists = true
    })
    
    -- Спейс для кеша новостной ленты
    local news_feed_cache = box.schema.space.create('news_feed_cache', {if_not_exists = true})
    news_feed_cache:format({
        {name = 'user_id', type = 'unsigned'},
        {name = 'post_id', type = 'unsigned'},
        {name = 'created_at', type = 'unsigned'},
        {name = 'data', type = 'map'}
    })
    news_feed_cache:create_index('primary', {
        parts = {'user_id', 'post_id'},
        type = 'HASH',
        unique = true,
        if_not_exists = true
    })
    news_feed_cache:create_index('user_feed', {
        parts = {'user_id', 'created_at'},
        type = 'TREE',
        unique = false,
        if_not_exists = true
    })
    
    -- Спейс для популярных постов
    local popular_posts = box.schema.space.create('popular_posts', {if_not_exists = true})
    popular_posts:format({
        {name = 'post_id', type = 'unsigned'},
        {name = 'score', type = 'number'},
        {name = 'data', type = 'map'},
        {name = 'updated_at', type = 'unsigned'}
    })
    popular_posts:create_index('primary', {
        parts = {'post_id'},
        type = 'HASH',
        unique = true,
        if_not_exists = true
    })
    popular_posts:create_index('by_score', {
        parts = {'score'},
        type = 'TREE',
        unique = false,
        if_not_exists = true
    })
    
    print("Tarantool spaces initialized successfully!")
end)

-- Функции для работы с данными
function get_user_feed(user_id, limit)
    limit = limit or 20
    local result = {}
    for _, tuple in box.space.news_feed_cache.index.user_feed:pairs({user_id}, {iterator = 'REQ'}) do
        if #result >= limit then
            break
        end
        table.insert(result, tuple)
    end
    return result
end

function get_popular_posts(limit)
    limit = limit or 10
    local result = {}
    for _, tuple in box.space.popular_posts.index.by_score:pairs(nil, {iterator = 'REQ'}) do
        if #result >= limit then
            break
        end
        table.insert(result, tuple)
    end
    return result
end

function cleanup_expired_sessions()
    local current_time = os.time()
    local expired = {}
    for _, tuple in box.space.user_sessions.index.expires_at:pairs() do
        if tuple[4] < current_time then
            table.insert(expired, tuple[1])
        end
    end
    for _, session_id in ipairs(expired) do
        box.space.user_sessions:delete(session_id)
    end
    return #expired
end

print("Tarantool configuration loaded successfully!")
