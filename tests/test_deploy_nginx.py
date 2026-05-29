from pathlib import Path


def test_nginx_routes_api_hostname_to_backend_health_surface():
    config = Path("deploy/nginx.conf").read_text()

    assert "server_name api.astracreates.com;" in config
    api_block = config.split("server_name api.astracreates.com;", 1)[1].split("server {", 1)[0]
    assert "location /" in api_block
    assert "proxy_pass http://backend" in api_block
    assert "server_name astracreates.com www.astracreates.com _;" in config


def test_certbot_supports_multi_domain_certificate():
    script = Path("deploy/certbot.sh").read_text()

    assert "PRIMARY_DOMAIN=" in script
    assert "DOMAIN_ARGS" in script
    assert 'for domain in "$@"' in script
