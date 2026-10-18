import os

cache_env = os.environ.get("CACHE_PATH", "tmp")
cache_path = (
    cache_env if os.path.isabs(cache_env) else os.path.join(os.getcwd(), cache_env)
)
dump_path = os.path.join(cache_path, "dump")
dump_org_path = os.path.join(cache_path, "dump_org")
img_path = os.path.join(cache_path, "img")
sitemap_file = "sitemap.xml"
robots_txt_file = "robots.txt"
sitemap_path = os.path.join(cache_path, sitemap_file)
robots_txt_path = os.path.join(cache_path, robots_txt_file)
