import tarantool

from app.core.config import settings

# Create a connection pool to Tarantool
def get_tarantool_connection():
    return tarantool.connect(
        host=settings.TARANTOOL_HOST,
        port=settings.TARANTOOL_PORT,
        user=settings.TARANTOOL_USER,
        password=settings.TARANTOOL_PASSWORD
    )

# Initialize Tarantool spaces and indexes
def init_tarantool():
    conn = get_tarantool_connection()
    
    # Create spaces if they don't exist
    # User sessions space
    conn.eval("""
        if not box.space.user_sessions then
            box.schema.space.create('user_sessions')
            box.space.user_sessions:format({
                {name = 'session_id', type = 'string'},
                {name = 'user_id', type = 'unsigned'},
                {name = 'data', type = 'map'},
                {name = 'expires_at', type = 'unsigned'}
            })
            box.space.user_sessions:create_index('primary', {
                parts = {'session_id'},
                type = 'HASH',
                unique = true
            })
            box.space.user_sessions:create_index('user_id', {
                parts = {'user_id'},
                type = 'TREE',
                unique = false
            })
            box.space.user_sessions:create_index('expires_at', {
                parts = {'expires_at'},
                type = 'TREE',
                unique = false
            })
        end
    """)
    
    # News feed cache space
    conn.eval("""
        if not box.space.news_feed_cache then
            box.schema.space.create('news_feed_cache')
            box.space.news_feed_cache:format({
                {name = 'user_id', type = 'unsigned'},
                {name = 'post_id', type = 'unsigned'},
                {name = 'created_at', type = 'unsigned'},
                {name = 'data', type = 'map'}
            })
            box.space.news_feed_cache:create_index('primary', {
                parts = {'user_id', 'post_id'},
                type = 'HASH',
                unique = true
            })
            box.space.news_feed_cache:create_index('user_feed', {
                parts = {'user_id', 'created_at'},
                type = 'TREE',
                unique = false
            })
        end
    """)
    
    # Popular posts cache space
    conn.eval("""
        if not box.space.popular_posts then
            box.schema.space.create('popular_posts')
            box.space.popular_posts:format({
                {name = 'post_id', type = 'unsigned'},
                {name = 'score', type = 'number'},
                {name = 'data', type = 'map'},
                {name = 'updated_at', type = 'unsigned'}
            })
            box.space.popular_posts:create_index('primary', {
                parts = {'post_id'},
                type = 'HASH',
                unique = true
            })
            box.space.popular_posts:create_index('by_score', {
                parts = {'score'},
                type = 'TREE',
                unique = false
            })
        end
    """)
    
    conn.close()