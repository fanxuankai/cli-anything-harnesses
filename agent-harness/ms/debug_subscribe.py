from cli_anything.ms.core.client import ConnectionConfig, MSClient
from cli_anything.ms.core.subscribe import SubscribeManager

MEDIA_TYPE = "tv"
NAME = "西游记"
YEAR = 1986
SEASON = 1

conn = ConnectionConfig.resolve()
print("configured =", conn.is_configured)
print("base_url =", conn.base_url)
print("config_path =", conn.DEFAULT_CONFIG_PATH)

client = MSClient(conn)
orig_request = client.request


def spy(method, path, **kwargs):
    print("\n==== REQUEST ====")
    print("METHOD:", method)
    print("PATH:", path)
    if kwargs.get("params") is not None:
        print("PARAMS:", kwargs["params"])
    if kwargs.get("json_body") is not None:
        print("JSON_BODY:", kwargs["json_body"])

    # 到真正保存前停住，避免创建真实订阅
    if path == "/api/v1/subscribe/save":
        raise SystemExit("stop before real subscribe/save")

    response = orig_request(method, path, **kwargs)
    print("STATUS:", response.status_code)
    print("CODE:", response.code)
    print("MESSAGE:", response.message)
    print("DATA:", response.data)
    return response


client.request = spy
mgr = SubscribeManager(client)

print("\n==== DEFAULT CONFIG ====")
cfg = mgr.get_default_config(MEDIA_TYPE)
print(cfg)

print("\n==== MERGED SUBSCRIBE PAYLOAD ====")
mgr.add(
    name=NAME,
    media_type=MEDIA_TYPE,
    year=YEAR,
    season=SEASON if MEDIA_TYPE == "tv" else None,
)
