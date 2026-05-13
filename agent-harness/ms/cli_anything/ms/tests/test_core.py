"""Unit tests for the ms CLI harness."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

from click.testing import CliRunner
import pytest


HARNESS_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
sys.path.insert(0, HARNESS_ROOT)

from cli_anything.ms.core.client import ApiResponse, ConnectionConfig, MSClient
from cli_anything.ms.core.cloud_resource import CloudResourceManager
from cli_anything.ms.core.download import DownloadManager
from cli_anything.ms.core.media import MEDIA_RANK_SOURCE_MAP, MEDIA_RECOMMEND_SOURCE_MAP, MEDIA_SOURCE_MAP, MediaManager
from cli_anything.ms.core.media_server import MediaServerManager
from cli_anything.ms.core.site import SiteManager
from cli_anything.ms.core.subscribe import SubscribeManager
from cli_anything.ms.core.system import SystemManager
from cli_anything.ms.ms_cli import main


def _mock_response(*, status_code=200, json_data=None, text_data=None):
    resp = MagicMock()
    resp.status_code = status_code
    resp.ok = 200 <= status_code < 400
    resp.text = text_data if text_data is not None else json.dumps(json_data or {})
    if json_data is None:
        resp.json.side_effect = ValueError("not json")
    else:
        resp.json.return_value = json_data
    return resp


def _raw_media_item(**overrides):
    item = {
        "id": "35010610",
        "title": "挽救计划",
        "subtitle": "",
        "source": 100,
        "type": "movie",
        "year": 2026,
        "vote": 8.6,
        "poster": "https://example.test/poster.jpg",
        "posterGif": "https://example.test/poster.gif",
        "backdrop": "https://example.test/backdrop.jpg",
        "overview": "2026 / 美国 / 剧情 科幻 惊悚",
        "rssId": 0,
        "downloaded": False,
        "publishedSites": ["天空", "馒头"],
        "archived": True,
        "archivedEffect": True,
        "archivedSeasons": [{"season": 1, "episodes": [1]}],
        "cloudStorageResourceCount": 2,
    }
    item.update(overrides)
    return item


def _normalized_media_item(**overrides):
    item = {
        "media_id": "35010610",
        "title": "挽救计划",
        "subtitle": "",
        "source": {"code": 100, "name": "豆瓣"},
        "media_type": "movie",
        "year": 2026,
        "vote": 8.6,
        "overview": "2026 / 美国 / 剧情 科幻 惊悚",
        "poster_url": "https://example.test/poster.jpg",
        "subscription": {"subscribed": False, "id": None},
        "library": {"archived": True, "resource_count": 2},
        "published_site_count": 2,
    }
    item.update(overrides)
    return item


def _raw_cloud_resource_item(**overrides):
    item = {
        "id": 0,
        "title": "庆余年.Joy.of.Life.2019.S01E46.1080p.mp4",
        "description": "1080p",
        "size": 2251076541,
        "pubDate": 1710000000,
        "mediaType": "tv",
        "tmdbId": 95842,
        "driverName": "115 Open",
        "linkDriverName": "",
        "linkType": 300,
        "enclosure": "ed2k://|file|test.mp4|2251076541|ABC|/",
        "csHashId": 1246925,
        "userName": "Lucifer",
        "userId": 931,
        "archived": True,
        "metadata": {
            "resourcePix": "1080p",
            "videoEncode": "AVC",
            "seasonEpisode": "S01 E46",
        },
        "tmdbMedia": {
            "id": 95842,
            "title": "庆余年",
            "year": 2019,
        },
    }
    item.update(overrides)
    return item


def _assert_no_raw_media_noise(item):
    for key in {
        "id",
        "type",
        "poster",
        "rssId",
        "archived",
        "cloudStorageResourceCount",
        "posterGif",
        "backdrop",
        "downloaded",
        "archivedEffect",
        "archivedSeasons",
        "publishedSites",
    }:
        assert key not in item


class TestConnectionConfig:

    def test_cli_has_highest_priority(self, monkeypatch, tmp_path):
        config_path = tmp_path / ".ms-cli.yaml"
        monkeypatch.setattr(ConnectionConfig, "DEFAULT_CONFIG_PATH", config_path)
        config_path.write_text("url: http://config\napi_key: config-key\n", encoding="utf-8")
        monkeypatch.setenv("MS_URL", "http://env")
        monkeypatch.setenv("MS_API_KEY", "env-key")

        conn = ConnectionConfig.resolve(url="http://cli", api_key="cli-key")

        assert conn.base_url == "http://cli"
        assert conn.api_key == "cli-key"
        assert conn.url_source == "cli"
        assert conn.api_key_source == "cli"

    def test_env_priority_over_config(self, monkeypatch, tmp_path):
        config_path = tmp_path / ".ms-cli.yaml"
        monkeypatch.setattr(ConnectionConfig, "DEFAULT_CONFIG_PATH", config_path)
        config_path.write_text("url: http://config\napi_key: config-key\n", encoding="utf-8")
        monkeypatch.setenv("MS_URL", "http://env")
        monkeypatch.setenv("MS_API_KEY", "env-key")

        conn = ConnectionConfig.resolve()

        assert conn.base_url == "http://env"
        assert conn.api_key == "env-key"
        assert conn.url_source == "env"
        assert conn.api_key_source == "env"

    def test_config_is_used_when_no_cli_or_env(self, monkeypatch, tmp_path):
        config_path = tmp_path / ".ms-cli.yaml"
        monkeypatch.setattr(ConnectionConfig, "DEFAULT_CONFIG_PATH", config_path)
        monkeypatch.delenv("MS_URL", raising=False)
        monkeypatch.delenv("MS_API_KEY", raising=False)
        config_path.write_text("url: http://config/\napi_key: saved-key\n", encoding="utf-8")

        conn = ConnectionConfig.resolve()

        assert conn.base_url == "http://config"
        assert conn.api_key == "saved-key"
        assert conn.url_source == "config"
        assert conn.api_key_source == "config"

    def test_save_and_mask(self, monkeypatch, tmp_path):
        config_path = tmp_path / ".ms-cli.yaml"
        monkeypatch.setattr(ConnectionConfig, "DEFAULT_CONFIG_PATH", config_path)

        saved_to = ConnectionConfig.save("http://localhost:8899/", "sk-1234567890")
        conn = ConnectionConfig.resolve()

        assert saved_to == config_path
        assert conn.base_url == "http://localhost:8899"
        assert conn.masked_api_key == "sk-1...7890"
        assert conn.is_configured is True

    def test_require_configured(self, monkeypatch, tmp_path):
        monkeypatch.setattr(ConnectionConfig, "DEFAULT_CONFIG_PATH", tmp_path / ".ms-cli.yaml")
        conn = ConnectionConfig.resolve()

        with pytest.raises(ValueError, match="URL is not configured"):
            conn.require_configured()


class TestApiResponse:

    def test_standard_response_is_unwrapped(self):
        response = _mock_response(
            json_data={"code": 0, "message": "ok", "data": {"status": "healthy"}},
        )

        normalized = ApiResponse.from_http_response(response)

        assert normalized.ok is True
        assert normalized.is_standard_response is True
        assert normalized.code == 0
        assert normalized.message == "ok"
        assert normalized.data == {"status": "healthy"}

    def test_mediasaber_success_code_is_treated_as_ok(self):
        response = _mock_response(
            json_data={"code": 20000, "message": "SUCCESS", "data": {"status": "healthy"}},
        )

        normalized = ApiResponse.from_http_response(response)

        assert normalized.ok is True
        assert normalized.code == 20000
        assert normalized.message == "SUCCESS"

    def test_non_standard_response_is_preserved(self):
        response = _mock_response(text_data="plain text body")

        normalized = ApiResponse.from_http_response(response)

        assert normalized.is_standard_response is False
        assert normalized.data == "plain text body"
        assert normalized.raw_body == "plain text body"


class TestMSClient:

    def test_build_url_requires_full_path(self):
        conn = ConnectionConfig.resolve(url="http://localhost:8899", api_key="key")
        client = MSClient(conn)

        with pytest.raises(ValueError, match="must start with '/'"):
            client.build_url("api/v1/system/status")

    @patch("cli_anything.ms.core.client.requests.Session")
    def test_request_sends_bearer_and_json(self, mock_session_cls):
        mock_session = MagicMock()
        mock_session.request.return_value = _mock_response(
            json_data={"code": 0, "message": "ok", "data": {"value": 1}},
        )
        mock_session_cls.return_value = mock_session

        conn = ConnectionConfig.resolve(url="http://localhost:8899", api_key="secret-token")
        client = MSClient(conn)
        response = client.request(
            "POST",
            "/api/v1/system/status",
            params={"verbose": "1"},
            headers={"X-Test": "true"},
            json_body={"hello": "world"},
        )

        assert response.ok is True
        mock_session.request.assert_called_once_with(
            method="POST",
            url="http://localhost:8899/api/v1/system/status",
            params={"verbose": "1"},
            headers={
                "Authorization": "Bearer secret-token",
                "X-Test": "true",
            },
            json={"hello": "world"},
            timeout=30,
        )


class TestSystemManager:

    def test_nas_info_uses_system_nas_info_endpoint(self):
        client = MagicMock()
        client.request.return_value = ApiResponse(
            status_code=200,
            ok=True,
            code=20000,
            message="SUCCESS",
            data=[{"instanceName": "bigbaby", "status": "online"}],
            raw_body={},
            is_standard_response=True,
        )

        result = SystemManager(client).nas_info()

        assert result == [{"instanceName": "bigbaby", "status": "online"}]
        client.request.assert_called_once_with("GET", "/api/v1/system/nas/info")

    def test_nas_info_rejects_unexpected_payload(self):
        client = MagicMock()
        client.request.return_value = ApiResponse(
            status_code=200,
            ok=True,
            code=20000,
            message="SUCCESS",
            data={"instanceName": "bigbaby"},
            raw_body={},
            is_standard_response=True,
        )

        with pytest.raises(ValueError, match="NAS info response data is not a list"):
            SystemManager(client).nas_info()

    def test_nas_info_surfaces_backend_error(self):
        client = MagicMock()
        client.request.return_value = ApiResponse(
            status_code=500,
            ok=False,
            code=50000,
            message="boom",
            data=None,
            raw_body={},
            is_standard_response=True,
        )

        with pytest.raises(ValueError, match="boom"):
            SystemManager(client).nas_info()


class TestMediaManager:

    def test_search_uses_media_search_endpoint(self):
        client = MagicMock()
        client.request.return_value = ApiResponse(
            status_code=200,
            ok=True,
            code=0,
            message="success",
            data={"total": 1, "pageNum": 1, "pageSize": 20, "list": [_raw_media_item(title="Test")]},
            raw_body={
                "code": 0,
                "message": "success",
                "data": {"total": 1, "pageNum": 1, "pageSize": 20, "list": [_raw_media_item(title="Test")]},
            },
            is_standard_response=True,
        )

        manager = MediaManager(client)
        result = manager.search(source_code=200, keyword="Interstellar", page=2, page_size=5)

        assert result["total"] == 1
        item = result["list"][0]
        assert item["media_id"] == "35010610"
        assert item["title"] == "Test"
        assert item["media_type"] == "movie"
        assert item["source"] == {"code": 100, "name": "豆瓣"}
        assert item["poster_url"] == "https://example.test/poster.jpg"
        assert item["subscription"] == {"subscribed": False, "id": None}
        assert item["library"] == {"archived": True, "resource_count": 2}
        assert item["published_site_count"] == 2
        _assert_no_raw_media_noise(item)
        client.request.assert_called_once_with(
            "GET",
            "/api/v1/media/search",
            params={
                "mediaSource": "200",
                "keyword": "Interstellar",
                "pageNum": "2",
                "pageSize": "5",
            },
        )

    def test_rank_sources_uses_media_subject_media_sources_endpoint(self):
        client = MagicMock()
        client.request.return_value = ApiResponse(
            status_code=200,
            ok=True,
            code=20000,
            message="SUCCESS",
            data=[{"value": 100, "text": "豆瓣"}],
            raw_body={},
            is_standard_response=True,
        )

        manager = MediaManager(client)
        result = manager.rank_sources()

        assert result == [{"value": 100, "text": "豆瓣"}]
        client.request.assert_called_once_with("GET", "/api/v1/mediaSubject/mediaSources")

    def test_rank_categories_uses_media_subject_categories_endpoint(self):
        client = MagicMock()
        client.request.return_value = ApiResponse(
            status_code=200,
            ok=True,
            code=20000,
            message="SUCCESS",
            data=[{"code": "douban_tv", "name": "📺 电视榜单", "custom": False}],
            raw_body={},
            is_standard_response=True,
        )

        manager = MediaManager(client)
        result = manager.rank_categories(100)

        assert result[0]["code"] == "douban_tv"
        client.request.assert_called_once_with("GET", "/api/v1/mediaSubject/categories/100")

    def test_rank_subjects_uses_media_subject_list_endpoint(self):
        client = MagicMock()
        client.request.return_value = ApiResponse(
            status_code=200,
            ok=True,
            code=20000,
            message="SUCCESS",
            data=[{"code": "tv_domestic", "name": "热播国产剧", "custom": False, "landscape": False}],
            raw_body={},
            is_standard_response=True,
        )

        manager = MediaManager(client)
        result = manager.rank_subjects("douban_tv")

        assert result[0]["code"] == "tv_domestic"
        client.request.assert_called_once_with(
            "GET",
            "/api/v1/mediaSubject/list",
            params={"categoryCode": "douban_tv"},
        )

    def test_rank_items_uses_media_subject_items_endpoint(self):
        client = MagicMock()
        client.request.return_value = ApiResponse(
            status_code=200,
            ok=True,
            code=20000,
            message="SUCCESS",
            data={"total": 50, "pageNum": 1, "pageSize": 25, "list": [_raw_media_item(title="危险关系", type="tv")]},
            raw_body={},
            is_standard_response=True,
        )

        manager = MediaManager(client)
        result = manager.rank_items(category_code="douban_tv", code="tv_domestic", page=1, page_size=25)

        assert result["total"] == 50
        assert result["list"][0]["media_type"] == "tv"
        assert result["list"][0]["title"] == "危险关系"
        _assert_no_raw_media_noise(result["list"][0])
        client.request.assert_called_once_with(
            "GET",
            "/api/v1/mediaSubject/items",
            params={
                "categoryCode": "douban_tv",
                "code": "tv_domestic",
                "pageNum": "1",
                "pageSize": "25",
            },
        )

    def test_media_items_normalize_subscription_and_site_counts(self):
        client = MagicMock()
        missing_rss_item = _raw_media_item(title="missing-rss-field", publishedSites=[])
        missing_rss_item.pop("rssId")
        client.request.return_value = ApiResponse(
            status_code=200,
            ok=True,
            code=20000,
            message="SUCCESS",
            data={
                "total": 5,
                "pageNum": 1,
                "pageSize": 5,
                "list": [
                    _raw_media_item(title="not-subscribed", rssId=0, publishedSites=None),
                    _raw_media_item(title="missing-rss", rssId=None, publishedSites=[]),
                    missing_rss_item,
                    _raw_media_item(title="subscribed-int", rssId=400, publishedSites=["天空"]),
                    _raw_media_item(title="subscribed-str", rssId="401", publishedSites=["天空", "馒头"]),
                ],
            },
            raw_body={},
            is_standard_response=True,
        )

        manager = MediaManager(client)
        result = manager.rank_items(category_code="douban_tv", code="tv_domestic", page=1, page_size=4)
        items = result["list"]

        assert items[0]["subscription"] == {"subscribed": False, "id": None}
        assert items[0]["published_site_count"] == 0
        assert items[1]["subscription"] == {"subscribed": False, "id": None}
        assert items[1]["published_site_count"] == 0
        assert items[2]["subscription"] == {"subscribed": False, "id": None}
        assert items[2]["published_site_count"] == 0
        assert items[3]["subscription"] == {"subscribed": True, "id": 400}
        assert items[3]["published_site_count"] == 1
        assert items[4]["subscription"] == {"subscribed": True, "id": "401"}
        assert items[4]["published_site_count"] == 2

    def test_rank_sources_rejects_non_list_payload(self):
        client = MagicMock()
        client.request.return_value = ApiResponse(
            status_code=200,
            ok=True,
            code=20000,
            message="SUCCESS",
            data={"value": 100},
            raw_body={},
            is_standard_response=True,
        )

        manager = MediaManager(client)

        with pytest.raises(ValueError, match="Media rank sources returned an unexpected response payload"):
            manager.rank_sources()

    def test_rank_items_rejects_non_dict_payload(self):
        client = MagicMock()
        client.request.return_value = ApiResponse(
            status_code=200,
            ok=True,
            code=20000,
            message="SUCCESS",
            data=[],
            raw_body={},
            is_standard_response=True,
        )

        manager = MediaManager(client)

        with pytest.raises(ValueError, match="Media rank items returned an unexpected response payload"):
            manager.rank_items(category_code="douban_tv", code="tv_domestic", page=1, page_size=20)

    def test_recommend_sources_uses_media_recommend_media_sources_endpoint(self):
        client = MagicMock()
        client.request.return_value = ApiResponse(
            status_code=200,
            ok=True,
            code=20000,
            message="SUCCESS",
            data=[{"value": 100, "text": "豆瓣"}],
            raw_body={},
            is_standard_response=True,
        )

        manager = MediaManager(client)
        result = manager.recommend_sources()

        assert result == [{"value": 100, "text": "豆瓣"}]
        client.request.assert_called_once_with("GET", "/api/v1/mediaRecommend/mediaSources")

    def test_recommend_channels_uses_media_recommend_channels_endpoint(self):
        client = MagicMock()
        client.request.return_value = ApiResponse(
            status_code=200,
            ok=True,
            code=20000,
            message="SUCCESS",
            data=[{"value": "movie", "text": "电影"}],
            raw_body={},
            is_standard_response=True,
        )

        manager = MediaManager(client)
        result = manager.recommend_channels(100)

        assert result[0]["value"] == "movie"
        client.request.assert_called_once_with("GET", "/api/v1/mediaRecommend/channels/100")

    def test_recommend_options_uses_media_recommend_options_endpoint(self):
        client = MagicMock()
        client.request.return_value = ApiResponse(
            status_code=200,
            ok=True,
            code=20000,
            message="SUCCESS",
            data=[{"id": "sort", "text": "排序", "options": [{"value": "", "text": "默认"}]}],
            raw_body={},
            is_standard_response=True,
        )

        manager = MediaManager(client)
        result = manager.recommend_options(media_source=100, channel="movie")

        assert result[0]["id"] == "sort"
        client.request.assert_called_once_with(
            "GET",
            "/api/v1/mediaRecommend/options",
            params={"mediaSource": "100", "channel": "movie"},
        )

    def test_recommend_items_uses_media_recommend_page_endpoint(self):
        client = MagicMock()
        client.request.return_value = ApiResponse(
            status_code=200,
            ok=True,
            code=20000,
            message="SUCCESS",
            data={"total": 50, "pageNum": 1, "pageSize": 25, "list": [_raw_media_item(title="危险关系", type="tv")]},
            raw_body={},
            is_standard_response=True,
        )

        manager = MediaManager(client)
        result = manager.recommend_items(
            media_source=200,
            channel="movie",
            options={"sort": "", "year": "", "tag": "", "country": ""},
            page=1,
            page_size=25,
        )

        assert result["total"] == 50
        assert result["list"][0]["media_type"] == "tv"
        assert result["list"][0]["title"] == "危险关系"
        _assert_no_raw_media_noise(result["list"][0])
        client.request.assert_called_once_with(
            "POST",
            "/api/v1/mediaRecommend/page",
            json_body={
                "mediaSource": 200,
                "channel": "movie",
                "options": {"sort": "", "year": "", "tag": "", "country": ""},
                "pageNum": 1,
                "pageSize": 25,
            },
        )

    def test_recommend_options_rejects_non_list_payload(self):
        client = MagicMock()
        client.request.return_value = ApiResponse(
            status_code=200,
            ok=True,
            code=20000,
            message="SUCCESS",
            data={},
            raw_body={},
            is_standard_response=True,
        )

        manager = MediaManager(client)

        with pytest.raises(ValueError, match="Media recommend options returned an unexpected response payload"):
            manager.recommend_options(media_source=100, channel="movie")

    def test_recommend_items_rejects_non_dict_payload(self):
        client = MagicMock()
        client.request.return_value = ApiResponse(
            status_code=200,
            ok=True,
            code=20000,
            message="SUCCESS",
            data=[],
            raw_body={},
            is_standard_response=True,
        )

        manager = MediaManager(client)

        with pytest.raises(ValueError, match="Media recommend items returned an unexpected response payload"):
            manager.recommend_items(media_source=200, channel="movie", options={}, page=1, page_size=20)


class TestMediaServerManager:

    def test_list_uses_media_server_list_endpoint(self):
        client = MagicMock()
        client.request.return_value = ApiResponse(
            status_code=200,
            ok=True,
            code=20000,
            message="SUCCESS",
            data=[
                {
                    "id": 1,
                    "name": "专线",
                    "type": 100,
                    "enabled": True,
                    "default": True,
                    "updatedAt": 1711266685,
                    "statistics": {
                        "id": 11,
                        "mediaServerId": 1,
                        "movieCount": 11980,
                        "tvCount": 2880,
                        "time": 107401,
                        "updatedAt": 1777132907,
                    },
                }
            ],
            raw_body={},
            is_standard_response=True,
        )

        result = MediaServerManager(client).list()

        assert result["total"] == 1
        assert result["items"][0]["type_text"] == "Emby"
        assert result["items"][0]["statistics"]["movie_count"] == 11980
        assert result["items"][0]["statistics"]["time_seconds"] == 107.401
        client.request.assert_called_once_with("GET", "/api/v1/mediaServer/list")

    def test_detail_libraries_statistics_and_media_items_use_expected_endpoints(self):
        client = MagicMock()
        client.request.side_effect = [
            ApiResponse(
                status_code=200,
                ok=True,
                code=20000,
                message="SUCCESS",
                data={"id": 1, "name": "专线", "type": 500, "enabled": True, "default": False},
                raw_body={},
                is_standard_response=True,
            ),
            ApiResponse(
                status_code=200,
                ok=True,
                code=20000,
                message="SUCCESS",
                data=[{"id": "lib-1", "name": "Movies", "paths": ["/media/movies"], "mediaType": "movie", "link": "http://example.test"}],
                raw_body={},
                is_standard_response=True,
            ),
            ApiResponse(
                status_code=200,
                ok=True,
                code=20000,
                message="SUCCESS",
                data={"mediaServerId": 1, "movieCount": 10, "tvCount": 2, "time": 1500},
                raw_body={},
                is_standard_response=True,
            ),
            ApiResponse(
                status_code=200,
                ok=True,
                code=20000,
                message="SUCCESS",
                data=[{"id": "p1", "name": "片名", "type": "movie", "link": "http://play.test", "percent": 42.5}],
                raw_body={},
                is_standard_response=True,
            ),
            ApiResponse(
                status_code=200,
                ok=True,
                code=20000,
                message="SUCCESS",
                data=[{"id": "l1", "name": "最新", "type": "tv", "link": "http://latest.test"}],
                raw_body={},
                is_standard_response=True,
            ),
            ApiResponse(
                status_code=200,
                ok=True,
                code=20000,
                message="SUCCESS",
                data=[{"id": "r1", "name": "继续", "type": "tv", "link": "http://resume.test", "percent": 80}],
                raw_body={},
                is_standard_response=True,
            ),
        ]

        manager = MediaServerManager(client)
        assert manager.detail(1)["type_text"] == "Plex"
        assert manager.libraries(1)["items"][0]["paths"] == ["/media/movies"]
        assert manager.statistics(1)["time_seconds"] == 1.5
        assert manager.playing(1)["items"][0]["percent"] == 42.5
        assert manager.latest(1, num=5)["items"][0]["name"] == "最新"
        assert manager.resume(1, num=6)["items"][0]["percent"] == 80.0

        client.request.assert_any_call("GET", "/api/v1/mediaServer/detail/1")
        client.request.assert_any_call("GET", "/api/v1/mediaServer/libraries/1")
        client.request.assert_any_call("GET", "/api/v1/mediaServerSync/statistics/1")
        client.request.assert_any_call("GET", "/api/v1/mediaServer/playing/1", params=None)
        client.request.assert_any_call("GET", "/api/v1/mediaServer/latest/1", params={"num": "5"})
        client.request.assert_any_call("GET", "/api/v1/mediaServer/resume/1", params={"num": "6"})

    def test_sync_items_passes_filters_and_normalizes_page(self):
        client = MagicMock()
        client.request.return_value = ApiResponse(
            status_code=200,
            ok=True,
            code=20000,
            message="SUCCESS",
            data={
                "total": 1,
                "pageNum": 2,
                "pageSize": 5,
                "list": [
                    {
                        "id": 99,
                        "mediaServerId": 1,
                        "libraryName": "电视剧",
                        "itemType": "tv",
                        "title": "猎罪图鉴",
                        "year": 2022,
                        "tmdbId": 139797,
                        "imdbId": "tt123",
                        "path": "/tv/猎罪图鉴",
                        "size": 2147483648,
                        "episodes": [{"season": 1, "episodes": [1, 2, 3, 5]}],
                        "missEps": True,
                        "createdAt": 1711266685,
                        "updatedAt": 1711266686,
                    }
                ],
            },
            raw_body={},
            is_standard_response=True,
        )

        result = MediaServerManager(client).sync_items(
            1,
            title="猎罪",
            media_type="tv",
            miss_eps=True,
            page=2,
            page_size=5,
        )

        assert result["total"] == 1
        assert result["list"][0]["title"] == "猎罪图鉴"
        assert result["list"][0]["size_text"] == "2.00 GB"
        assert result["list"][0]["episodes_text"] == "S01:E1-3, E5"
        client.request.assert_called_once_with(
            "GET",
            "/api/v1/mediaServerSync/items/1",
            params={
                "pageNum": "2",
                "pageSize": "5",
                "title": "猎罪",
                "mediaType": "tv",
                "missEps": "true",
            },
        )

    def test_sync_run_submits_server_sync(self):
        client = MagicMock()
        client.request.return_value = ApiResponse(
            status_code=200,
            ok=True,
            code=20000,
            message="SUCCESS",
            data=True,
            raw_body={},
            is_standard_response=True,
        )

        result = MediaServerManager(client).sync_run(1)

        assert result["status"] == "submitted"
        assert result["server_id"] == 1
        client.request.assert_called_once_with("GET", "/api/v1/mediaServerSync/run/1")

    def test_media_server_methods_reject_unexpected_payloads(self):
        client = MagicMock()
        client.request.return_value = ApiResponse(
            status_code=200,
            ok=True,
            code=20000,
            message="SUCCESS",
            data={"not": "a-list"},
            raw_body={},
            is_standard_response=True,
        )

        with pytest.raises(ValueError, match="Media server list returned an unexpected response payload"):
            MediaServerManager(client).list()

        client.request.return_value = ApiResponse(
            status_code=200,
            ok=True,
            code=20000,
            message="SUCCESS",
            data=[],
            raw_body={},
            is_standard_response=True,
        )
        with pytest.raises(ValueError, match="Media server sync items returned an unexpected response payload"):
            MediaServerManager(client).sync_items(1)

    def test_miss_episodes_check_uses_media_server_endpoint(self):
        client = MagicMock()
        client.request.return_value = ApiResponse(
            status_code=200,
            ok=True,
            code=20000,
            message="SUCCESS",
            data=[
                {
                    "tmdbId": 139797,
                    "mediaType": "tv",
                    "title": "猎罪图鉴",
                    "year": 2022,
                    "episodes": [
                        {
                            "season": 1,
                            "totalEpisodes": 20,
                            "missEpisodes": [7],
                        }
                    ],
                }
            ],
            raw_body={},
            is_standard_response=True,
        )

        manager = MediaServerManager(client)
        result = manager.miss_episodes_check()

        assert result["total"] == 1
        assert result["items"][0]["title"] == "猎罪图鉴"
        client.request.assert_called_once_with("GET", "/api/v1/mediaServer/missEpisodesCheck")

    def test_miss_episodes_check_limits_to_first_twenty_items(self):
        client = MagicMock()
        client.request.return_value = ApiResponse(
            status_code=200,
            ok=True,
            code=20000,
            message="SUCCESS",
            data=[
                {
                    "tmdbId": idx,
                    "mediaType": "tv",
                    "title": f"title-{idx}",
                    "year": 2020,
                    "episodes": [],
                }
                for idx in range(25)
            ],
            raw_body={},
            is_standard_response=True,
        )

        manager = MediaServerManager(client)
        result = manager.miss_episodes_check()

        assert result["total"] == 25
        assert len(result["items"]) == 20
        assert result["items"][0]["title"] == "title-0"
        assert result["items"][-1]["title"] == "title-19"


class TestSiteManager:

    def test_list_uses_site_list_endpoint_and_redacts_sensitive_fields(self):
        client = MagicMock()
        client.request.return_value = ApiResponse(
            status_code=200,
            ok=True,
            code=20000,
            message="SUCCESS",
            data=[
                {
                    "id": 1,
                    "code": "mteam",
                    "name": "馒头",
                    "enabled": True,
                    "priority": 1,
                    "userId": "user-1",
                    "domainDisplay": "https://example.test",
                    "cookie": "secret-cookie",
                    "signIn": True,
                    "statistic": True,
                    "search": True,
                    "message": False,
                }
            ],
            raw_body={},
            is_standard_response=True,
        )

        result = SiteManager(client).list(name="馒头", enabled=True, switch_type="sign-in")

        assert result["total"] == 1
        assert result["items"][0]["name"] == "馒头"
        assert result["items"][0]["switches"]["sign_in"] is True
        assert "cookie" not in result["items"][0]
        client.request.assert_called_once_with(
            "GET",
            "/api/v1/site/list",
            params={"name": "馒头", "enabled": "true", "type": "600"},
        )

    def test_data_total_and_latest_use_site_data_endpoints(self):
        client = MagicMock()
        client.request.side_effect = [
            ApiResponse(
                status_code=200,
                ok=True,
                code=20000,
                message="SUCCESS",
                data={
                    "uploaded": 1099511627776,
                    "downloaded": 536870912,
                    "bonus": 12345.6,
                    "seedingCount": 88,
                    "seedingSize": 2147483648,
                },
                raw_body={},
                is_standard_response=True,
            ),
            ApiResponse(
                status_code=200,
                ok=True,
                code=20000,
                message="SUCCESS",
                data=[
                    {
                        "id": 10,
                        "siteId": 1,
                        "siteCode": "mteam",
                        "siteName": "馒头",
                        "siteDomainDisplay": "https://example.test",
                        "isLogin": True,
                        "signedIn": False,
                        "ratio": 2.5,
                        "uploaded": 1024,
                        "downloaded": 512,
                        "bonus": 99,
                        "seedingCount": 3,
                        "seedingSize": 2048,
                        "todayUploaded": 128,
                        "todayDownloaded": 64,
                        "statisticDate": "2026-04-26",
                    }
                ],
                raw_body={},
                is_standard_response=True,
            ),
        ]

        manager = SiteManager(client)
        total = manager.data_total()
        latest = manager.data_latest(site_id=1, site_name="馒头", order_by="uploaded", order_direction="desc")

        assert total["uploaded_text"] == "1.00 TB"
        assert latest["items"][0]["site_name"] == "馒头"
        assert latest["items"][0]["uploaded_text"] == "1.00 KB"
        client.request.assert_any_call("GET", "/api/v1/siteData/total")
        client.request.assert_any_call(
            "GET",
            "/api/v1/siteData/latest",
            params={"siteId": "1", "siteName": "馒头", "orderBy": "uploaded", "orderDirection": "desc"},
        )

    def test_sign_in_history_and_go_use_expected_endpoints(self):
        client = MagicMock()
        client.request.side_effect = [
            ApiResponse(
                status_code=200,
                ok=True,
                code=20000,
                message="SUCCESS",
                data={
                    "total": 1,
                    "pageNum": 2,
                    "pageSize": 5,
                    "list": [
                        {
                            "id": 7,
                            "siteId": 1,
                            "siteCode": "mteam",
                            "siteName": "馒头",
                            "code": 100,
                            "content": "签到成功",
                            "createdAt": 1777132907,
                        }
                    ],
                },
                raw_body={},
                is_standard_response=True,
            ),
            ApiResponse(
                status_code=200,
                ok=True,
                code=20000,
                message="SUCCESS",
                data=True,
                raw_body={},
                is_standard_response=True,
            ),
        ]

        manager = SiteManager(client)
        history = manager.sign_in_history(site_name="馒头", page=2, page_size=5)
        submitted = manager.sign_in(site_ids=[1, 2])

        assert history["list"][0]["code_text"] == "签到成功"
        assert submitted["status"] == "submitted"
        assert submitted["site_ids"] == [1, 2]
        client.request.assert_any_call(
            "GET",
            "/api/v1/siteSignIn/page",
            params={"pageNum": "2", "pageSize": "5", "siteName": "馒头"},
        )
        client.request.assert_any_call("POST", "/api/v1/siteSignIn/go", json_body={"ids": [1, 2]})

    def test_site_methods_reject_unexpected_payloads(self):
        client = MagicMock()
        client.request.return_value = ApiResponse(
            status_code=200,
            ok=True,
            code=20000,
            message="SUCCESS",
            data={"not": "a-list"},
            raw_body={},
            is_standard_response=True,
        )

        with pytest.raises(ValueError, match="Site list returned an unexpected response payload"):
            SiteManager(client).list()

        client.request.return_value = ApiResponse(
            status_code=200,
            ok=True,
            code=20000,
            message="SUCCESS",
            data=[],
            raw_body={},
            is_standard_response=True,
        )
        with pytest.raises(ValueError, match="Site data total returned an unexpected response payload"):
            SiteManager(client).data_total()


class TestDownloadManager:

    def test_downloaders_uses_downloader_list_and_redacts_config(self):
        client = MagicMock()
        client.request.return_value = ApiResponse(
            status_code=200,
            ok=True,
            code=20000,
            message="SUCCESS",
            data=[
                {
                    "id": 1,
                    "type": 100,
                    "name": "qb",
                    "enabled": True,
                    "default": True,
                    "remark": "main",
                    "config": {
                        "url": "http://qb.test",
                        "username": "admin",
                        "password": "secret",
                        "monitor": "/downloads",
                        "moveMode": "copy",
                    },
                    "createdAt": 1777132907,
                }
            ],
            raw_body={},
            is_standard_response=True,
        )

        result = DownloadManager(client).downloaders()

        assert result["total"] == 1
        assert result["items"][0]["name"] == "qb"
        assert result["items"][0]["url"] == "http://qb.test"
        assert "password" not in result["items"][0]
        client.request.assert_called_once_with("GET", "/api/v1/downloader/list")

    def test_downloading_uses_download_ids_and_normalizes_items(self):
        client = MagicMock()
        client.request.return_value = ApiResponse(
            status_code=200,
            ok=True,
            code=20000,
            message="SUCCESS",
            data=[
                {
                    "id": "abc",
                    "title": "流浪地球",
                    "mediaType": "movie",
                    "year": 2019,
                    "seasonEpisode": "",
                    "speed": 1048576,
                    "progress": 0.456,
                    "state": "downloading",
                    "paused": False,
                    "torrentTitle": "torrent title",
                    "savePath": "/downloads",
                    "siteId": 2,
                    "siteName": "馒头",
                }
            ],
            raw_body={},
            is_standard_response=True,
        )

        result = DownloadManager(client).downloading(download_ids=["abc"])

        assert result["total"] == 1
        assert result["items"][0]["speed_text"] == "1.00 MB/s"
        assert result["items"][0]["progress_percent"] == 45.6
        client.request.assert_called_once_with("POST", "/api/v1/download/downloading", json_body={"downloadIds": ["abc"]})

    def test_history_uses_filters_and_normalizes_page(self):
        client = MagicMock()
        client.request.return_value = ApiResponse(
            status_code=200,
            ok=True,
            code=20000,
            message="SUCCESS",
            data={
                "total": 1,
                "pageNum": 2,
                "pageSize": 5,
                "list": [
                    {
                        "id": 10,
                        "title": "庆余年",
                        "mediaType": "tv",
                        "year": 2019,
                        "tmdbId": 95842,
                        "siteId": 2,
                        "siteName": "馒头",
                        "torrentTitle": "torrent",
                        "seasonEpisode": "S01E01",
                        "savePath": "/downloads",
                        "downloadId": "hash",
                        "createdAt": 1777132907,
                    }
                ],
            },
            raw_body={},
            is_standard_response=True,
        )

        result = DownloadManager(client).history(
            title="庆余年",
            media_type="tv",
            site_id=2,
            site_name="馒头",
            page=2,
            page_size=5,
        )

        assert result["total"] == 1
        assert result["list"][0]["download_id"] == "hash"
        client.request.assert_called_once_with(
            "GET",
            "/api/v1/download/history",
            params={
                "pageNum": "2",
                "pageSize": "5",
                "title": "庆余年",
                "mediaType": "tv",
                "siteId": "2",
                "siteName": "馒头",
            },
        )

    def test_pause_resume_delete_use_expected_endpoints(self):
        client = MagicMock()
        client.request.return_value = ApiResponse(
            status_code=200,
            ok=True,
            code=20000,
            message="SUCCESS",
            data=True,
            raw_body={},
            is_standard_response=True,
        )

        manager = DownloadManager(client)
        assert manager.pause("abc")["action"] == "pause"
        assert manager.resume("abc")["action"] == "resume"
        assert manager.delete("abc", delete_file=True)["action"] == "delete"

        client.request.assert_any_call("GET", "/api/v1/download/pause/abc", params=None)
        client.request.assert_any_call("GET", "/api/v1/download/resume/abc", params=None)
        client.request.assert_any_call("DELETE", "/api/v1/download/delete/abc", params={"deleteFile": "true"})

    def test_download_methods_reject_unexpected_payloads(self):
        client = MagicMock()
        client.request.return_value = ApiResponse(
            status_code=200,
            ok=True,
            code=20000,
            message="SUCCESS",
            data={"not": "a-list"},
            raw_body={},
            is_standard_response=True,
        )

        with pytest.raises(ValueError, match="Downloader list returned an unexpected response payload"):
            DownloadManager(client).downloaders()

        client.request.return_value = ApiResponse(
            status_code=200,
            ok=True,
            code=20000,
            message="SUCCESS",
            data=[],
            raw_body={},
            is_standard_response=True,
        )
        with pytest.raises(ValueError, match="Download history returned an unexpected response payload"):
            DownloadManager(client).history()


class TestCloudResourceManager:

    def test_search_uses_site_resource_page_endpoint(self):
        client = MagicMock()
        client.request.return_value = ApiResponse(
            status_code=200,
            ok=True,
            code=20000,
            message="SUCCESS",
            data={"total": 1, "pageNum": 2, "pageSize": 5, "list": [_raw_cloud_resource_item()]},
            raw_body={},
            is_standard_response=True,
        )

        manager = CloudResourceManager(client)
        result = manager.search(
            keyword="庆余年",
            tmdb_id=95842,
            media_type="tv",
            season=1,
            episode=46,
            begin_episode=40,
            end_episode=46,
            creator_id=931,
            page=2,
            page_size=5,
        )

        assert result["total"] == 1
        item = result["list"][0]
        assert item["title"].startswith("庆余年")
        assert item["size"] == 2251076541
        assert item["driver"]["name"] == "115 Open"
        assert item["creator"] == {"id": 931, "name": "Lucifer"}
        assert item["tmdb_id"] == 95842
        assert item["link"] == {
            "type": 300,
            "type_name": "云下载",
            "url": "ed2k://|file|test.mp4|2251076541|ABC|/",
        }
        assert item["cs_hash_id"] == 1246925
        assert item["downloadable"] is True
        assert item["download_request"] == {
            "type": 300,
            "contents": ["ed2k://|file|test.mp4|2251076541|ABC|/"],
            "csHashId": 1246925,
            "csCreator": "Lucifer",
        }
        client.request.assert_called_once_with(
            "POST",
            "/api/v1/siteResource/page",
            params={"pageNum": "2", "pageSize": "5"},
            json_body={
                "searchCloudStorage": True,
                "keyword": "庆余年",
                "tmdbId": 95842,
                "mediaType": "tv",
                "season": 1,
                "episode": 46,
                "beginEpisode": 40,
                "endEpisode": 46,
                "creatorId": 931,
            },
        )

    def test_search_requires_meaningful_query(self):
        manager = CloudResourceManager(MagicMock())

        with pytest.raises(ValueError, match="requires --keyword"):
            manager.search(page=1, page_size=25)

    def test_tmdb_search_requires_media_type(self):
        manager = CloudResourceManager(MagicMock())

        with pytest.raises(ValueError, match="requires --type"):
            manager.search(tmdb_id=95842, page=1, page_size=25)

    def test_share_link_download_request_uses_share_receive_type(self):
        client = MagicMock()
        client.request.return_value = ApiResponse(
            status_code=200,
            ok=True,
            code=20000,
            message="SUCCESS",
            data={"total": 1, "pageNum": 1, "pageSize": 25, "list": [_raw_cloud_resource_item(linkType=200, enclosure='{"path":"test.mp4"}')]},
            raw_body={},
            is_standard_response=True,
        )

        result = CloudResourceManager(client).search(keyword="庆余年")

        assert result["list"][0]["link"]["type_name"] == "云分享"
        assert result["list"][0]["download_request"]["type"] == 200
        assert result["list"][0]["download_request"]["contents"] == ['{"path":"test.mp4"}']

    def test_submit_download_posts_upload_payload_for_offline_download(self):
        client = MagicMock()
        client.request.return_value = ApiResponse(
            status_code=200,
            ok=True,
            code=20000,
            message="SUCCESS",
            data=True,
            raw_body={},
            is_standard_response=True,
        )
        request = {
            "type": 300,
            "contents": ["ed2k://|file|test.mp4|1|ABC|/"],
            "csHashId": 1246925,
            "csCreator": "Lucifer",
        }

        result = CloudResourceManager(client).submit_download(request, dir_path="/downloads")

        assert result["status"] == "submitted"
        assert result["type"] == 300
        assert result["count"] == 1
        client.request.assert_called_once_with(
            "POST",
            "/api/v1/cloudStorageFs/upload",
            json_body={
                "type": 300,
                "contents": ["ed2k://|file|test.mp4|1|ABC|/"],
                "dir": "/downloads",
                "csHashId": 1246925,
                "csCreator": "Lucifer",
            },
        )

    def test_submit_download_posts_upload_payload_for_share_receive(self):
        client = MagicMock()
        client.request.return_value = ApiResponse(
            status_code=200,
            ok=True,
            code=20000,
            message="SUCCESS",
            data=True,
            raw_body={},
            is_standard_response=True,
        )

        CloudResourceManager(client).submit_download(
            {"type": 200, "contents": ['{"path":"test.mp4"}']},
            dir_path=None,
        )

        client.request.assert_called_once_with(
            "POST",
            "/api/v1/cloudStorageFs/upload",
            json_body={"type": 200, "contents": ['{"path":"test.mp4"}']},
        )

    def test_submit_download_rejects_invalid_request(self):
        manager = CloudResourceManager(MagicMock())

        with pytest.raises(ValueError, match="must be 200 or 300"):
            manager.submit_download({"type": 100, "contents": ["x"]}, dir_path=None)
        with pytest.raises(ValueError, match="non-empty array"):
            manager.submit_download({"type": 300, "contents": []}, dir_path=None)

    def test_rank_fetches_list_and_mine(self):
        client = MagicMock()
        client.request.side_effect = [
            ApiResponse(
                status_code=200,
                ok=True,
                code=20000,
                message="SUCCESS",
                data=[
                    {"creator_id": 931, "creator": "Lucifer", "count": 2030, "size": 1099511627776},
                    {"creatorId": 932, "creator": "清酒", "count": 1808, "size": 5368709120},
                ],
                raw_body={},
                is_standard_response=True,
            ),
            ApiResponse(
                status_code=200,
                ok=True,
                code=20000,
                message="SUCCESS",
                data={"creator_id": 99, "creator": "我", "count": 5, "size": 1048576, "rank": 20, "surpass_percent": 39.39},
                raw_body={},
                is_standard_response=True,
            ),
        ]

        result = CloudResourceManager(client).rank(range_type="today", stat_type="size", refresh=True)

        assert result["range_type"] == "today"
        assert result["stat_type"] == "size"
        assert result["items"][0] == {
            "rank": 1,
            "creator_id": 931,
            "creator": "Lucifer",
            "count": 2030,
            "size": 1099511627776,
            "size_text": "1.00 TB",
            "value": 1099511627776,
            "value_text": "1.00 TB",
        }
        assert result["items"][1]["creator_id"] == 932
        assert result["mine"]["rank"] == 20
        assert result["mine"]["surpass_percent"] == 39.39
        assert result["mine"]["value_text"] == "1.00 MB"
        assert client.request.call_args_list[0].args == ("GET", "/api/v1/system/hashReportStatistic")
        assert client.request.call_args_list[0].kwargs == {
            "params": {"rangeType": "today", "statType": "size", "refresh": "true"}
        }
        assert client.request.call_args_list[1].args == ("GET", "/api/v1/system/hashReportStatisticMine")
        assert client.request.call_args_list[1].kwargs == {
            "params": {"rangeType": "today", "statType": "size", "refresh": "true"}
        }

    def test_rank_count_value_uses_count(self):
        client = MagicMock()
        client.request.side_effect = [
            ApiResponse(status_code=200, ok=True, code=20000, message="SUCCESS", data=[{"creator": "小汐", "count": 2030, "size": 1}], raw_body={}, is_standard_response=True),
            ApiResponse(status_code=200, ok=True, code=20000, message="SUCCESS", data={"count": 5, "size": 1, "rank": 20, "surpassPercent": 39.39}, raw_body={}, is_standard_response=True),
        ]

        result = CloudResourceManager(client).rank(range_type="week", stat_type="count", refresh=False)

        assert result["items"][0]["value"] == 2030
        assert result["items"][0]["value_text"] == "2030 次"
        assert result["mine"]["surpass_percent"] == 39.39
        assert result["mine"]["value_text"] == "5 次"

    def test_rank_rejects_invalid_options(self):
        manager = CloudResourceManager(MagicMock())

        with pytest.raises(ValueError, match="--range must be today"):
            manager.rank(range_type="month", stat_type="count")
        with pytest.raises(ValueError, match="--stat must be count"):
            manager.rank(range_type="today", stat_type="score")

    def test_rank_rejects_unexpected_payloads(self):
        client = MagicMock()
        client.request.return_value = ApiResponse(
            status_code=200,
            ok=True,
            code=20000,
            message="SUCCESS",
            data={"bad": "payload"},
            raw_body={},
            is_standard_response=True,
        )

        with pytest.raises(ValueError, match="unexpected response payload"):
            CloudResourceManager(client).rank(range_type="today", stat_type="count")

        client = MagicMock()
        client.request.side_effect = [
            ApiResponse(status_code=200, ok=True, code=20000, message="SUCCESS", data=[], raw_body={}, is_standard_response=True),
            ApiResponse(status_code=200, ok=True, code=20000, message="SUCCESS", data=[], raw_body={}, is_standard_response=True),
        ]

        with pytest.raises(ValueError, match="rank mine returned an unexpected response payload"):
            CloudResourceManager(client).rank(range_type="today", stat_type="count")


class TestSubscribeManager:

    def test_get_default_config_uses_detail_endpoint(self):
        client = MagicMock()
        client.request.return_value = ApiResponse(
            status_code=200,
            ok=True,
            code=0,
            message="success",
            data={"type": "movie", "downloaderId": 1},
            raw_body={"code": 0, "message": "success", "data": {"type": "movie", "downloaderId": 1}},
            is_standard_response=True,
        )

        manager = SubscribeManager(client)
        result = manager.get_default_config("movie")

        assert result == {"type": "movie", "downloaderId": 1}
        client.request.assert_called_once_with("GET", "/api/v1/subscribeDefaultConfig/detail/movie")

    def test_add_fetches_default_config_then_saves(self):
        client = MagicMock()
        client.request.side_effect = [
            ApiResponse(
                status_code=200,
                ok=True,
                code=0,
                message="success",
                data={
                    "type": "tv",
                    "filterRuleId": 10,
                    "torrentSortId": 20,
                    "downloaderId": 1,
                    "downloaderParamsId": 2,
                    "downloaderDirectoryId": 3,
                    "rssSites": [11],
                    "searchSites": [22],
                    "autoUpdateTotalEpisode": True,
                    "include": "HDR",
                    "exclude": "CAM",
                    "subCloudStorage": False,
                    "subCloudStoragePath": "/cloud",
                    "csCreatorIds": "1,2",
                    "mediums": ["BluRay"],
                },
                raw_body={},
                is_standard_response=True,
            ),
            ApiResponse(
                status_code=200,
                ok=True,
                code=0,
                message="success",
                data=None,
                raw_body={"code": 0, "message": "success", "data": None},
                is_standard_response=True,
            ),
        ]

        manager = SubscribeManager(client)
        result = manager.add(name="Breaking Bad", media_type="tv", year=2008, season=1)

        assert result["status"] == "ok"
        assert result["subscribe"]["season"] == 1
        assert result["subscribe"]["filterRuleId"] == 10
        assert "mediums" not in result["subscribe"]
        assert client.request.call_args_list[1].kwargs["json_body"]["searchSites"] == [22]

    def test_page_uses_subscribe_page_endpoint(self):
        client = MagicMock()
        client.request.return_value = ApiResponse(
            status_code=200,
            ok=True,
            code=20000,
            message="SUCCESS",
            data={"total": 1, "pageNum": 1, "pageSize": 99, "list": [{"name": "Interstellar"}]},
            raw_body={},
            is_standard_response=True,
        )

        manager = SubscribeManager(client)
        result = manager.page(media_type="movie", page=1, page_size=99)

        assert result["total"] == 1
        client.request.assert_called_once_with(
            "GET",
            "/api/v1/subscribe/page",
            params={
                "type": "movie",
                "pageNum": "1",
                "pageSize": "99",
            },
        )

    def test_page_rejects_non_dict_payload(self):
        client = MagicMock()
        client.request.return_value = ApiResponse(
            status_code=200,
            ok=True,
            code=20000,
            message="SUCCESS",
            data=[],
            raw_body={},
            is_standard_response=True,
        )

        manager = SubscribeManager(client)

        with pytest.raises(ValueError, match="Subscribe page returned an unexpected response payload"):
            manager.page(media_type="movie", page=1, page_size=20)


class TestCLI:

    def test_help_without_tty_shows_help(self):
        runner = CliRunner()
        result = runner.invoke(main, [])

        assert result.exit_code == 0
        assert "Usage:" in result.output

    def test_show_connection_json(self, monkeypatch, tmp_path):
        monkeypatch.setattr(ConnectionConfig, "DEFAULT_CONFIG_PATH", tmp_path / ".ms-cli.yaml")
        ConnectionConfig.save("http://localhost:8899", "secret-key")

        runner = CliRunner()
        result = runner.invoke(main, ["--json", "config", "show-connection"])

        assert result.exit_code == 0
        payload = json.loads(result.output)
        assert payload["configured"] is True
        assert payload["base_url"] == "http://localhost:8899"
        assert payload["api_key"] == "secr...-key"

    def test_system_nas_info_json(self, monkeypatch):
        runner = CliRunner()

        def fake_nas_info(self):
            return [
                {
                    "pluginCode": "ugreen_service_assistant",
                    "instanceName": "bigbaby",
                    "vendor": "ugreen",
                    "status": "online",
                }
            ]

        monkeypatch.setattr(SystemManager, "nas_info", fake_nas_info)
        result = runner.invoke(
            main,
            [
                "--url",
                "http://localhost:8899",
                "--apikey",
                "secret-key",
                "--json",
                "system",
                "nas-info",
            ],
        )

        assert result.exit_code == 0
        payload = json.loads(result.output)
        assert payload == [
            {
                "pluginCode": "ugreen_service_assistant",
                "instanceName": "bigbaby",
                "vendor": "ugreen",
                "status": "online",
            }
        ]

    def test_system_nas_info_surfaces_backend_error(self, monkeypatch):
        runner = CliRunner()

        def fake_nas_info(self):
            raise ValueError("boom")

        monkeypatch.setattr(SystemManager, "nas_info", fake_nas_info)
        result = runner.invoke(
            main,
            [
                "--url",
                "http://localhost:8899",
                "--apikey",
                "secret-key",
                "--json",
                "system",
                "nas-info",
            ],
        )

        assert result.exit_code == 1
        assert json.loads(result.output) == {"error": "boom"}

    def test_media_search_command_normalized_json(self, monkeypatch):
        runner = CliRunner()

        def fake_search(self, source_code, keyword, page, page_size):
            assert source_code == MEDIA_SOURCE_MAP["tmdb"]
            assert keyword == "Interstellar"
            assert page == 1
            assert page_size == 20
            return {
                "total": 1,
                "pageNum": 1,
                "pageSize": 20,
                "list": [
                    _normalized_media_item(
                        media_id="1889243",
                        title="Interstellar",
                        subtitle="星际穿越",
                        source={"code": 200, "name": "TMDB"},
                        media_type="movie",
                        year=2014,
                        vote=8.6,
                    )
                ],
            }

        monkeypatch.setattr(MediaManager, "search", fake_search)
        result = runner.invoke(
            main,
            [
                "--url",
                "http://localhost:8899",
                "--apikey",
                "secret-key",
                "--json",
                "media",
                "search",
                "--source",
                "tmdb",
                "--keyword",
                "Interstellar",
            ],
        )

        assert result.exit_code == 0
        payload = json.loads(result.output)
        assert payload["total"] == 1
        assert payload["list"][0]["title"] == "Interstellar"
        assert payload["list"][0]["media_id"] == "1889243"
        assert payload["list"][0]["media_type"] == "movie"
        assert "rssId" not in payload["list"][0]

    def test_media_search_command_human_output(self, monkeypatch):
        runner = CliRunner()

        def fake_search(self, source_code, keyword, page, page_size):
            return {
                "total": 1,
                "pageNum": 1,
                "pageSize": 20,
                "list": [
                    _normalized_media_item(
                        media_id="1889243",
                        title="Interstellar",
                        subtitle="星际穿越",
                        source={"code": 200, "name": "TMDB"},
                        media_type="movie",
                        year=2014,
                        vote=8.6,
                    )
                ],
            }

        monkeypatch.setattr(MediaManager, "search", fake_search)
        result = runner.invoke(
            main,
            [
                "--url",
                "http://localhost:8899",
                "--apikey",
                "secret-key",
                "media",
                "search",
                "--source",
                "tmdb",
                "--keyword",
                "Interstellar",
            ],
        )

        assert result.exit_code == 0
        assert "Media Search" in result.output
        assert "Interstellar" in result.output
        assert "TMDB" in result.output

    def test_media_search_command_empty_result(self, monkeypatch):
        runner = CliRunner()

        monkeypatch.setattr(
            MediaManager,
            "search",
            lambda self, source_code, keyword, page, page_size: {
                "total": 0,
                "pageNum": 1,
                "pageSize": 20,
                "list": [],
            },
        )

        result = runner.invoke(
            main,
            [
                "--url",
                "http://localhost:8899",
                "--apikey",
                "secret-key",
                "media",
                "search",
                "--source",
                "douban",
                "--keyword",
                "霸王别姬",
            ],
        )

        assert result.exit_code == 0
        assert "(空)" in result.output

    def test_media_search_requires_valid_source(self):
        runner = CliRunner()
        result = runner.invoke(
            main,
            [
                "--url",
                "http://localhost:8899",
                "--apikey",
                "secret-key",
                "media",
                "search",
                "--source",
                "unknown",
                "--keyword",
                "foo",
            ],
        )

        assert result.exit_code != 0
        assert "Invalid value for '--source'" in result.output

    def test_media_search_rejects_empty_keyword(self):
        runner = CliRunner()
        result = runner.invoke(
            main,
            [
                "--url",
                "http://localhost:8899",
                "--apikey",
                "secret-key",
                "media",
                "search",
                "--source",
                "tmdb",
                "--keyword",
                "   ",
            ],
        )

        assert result.exit_code != 0
        assert "--keyword cannot be empty" in result.output

    def test_cloud_resource_search_command_json(self, monkeypatch):
        runner = CliRunner()

        def fake_search(
            self,
            *,
            keyword,
            tmdb_id,
            media_type,
            season,
            episode,
            begin_episode,
            end_episode,
            creator_id,
            page,
            page_size,
        ):
            assert keyword == "庆余年"
            assert tmdb_id is None
            assert media_type is None
            assert season is None
            assert episode is None
            assert begin_episode is None
            assert end_episode is None
            assert creator_id is None
            assert page == 1
            assert page_size == 25
            return {
                "total": 1,
                "pageNum": 1,
                "pageSize": 25,
                "list": [
                    {
                        "title": "庆余年.S01E46.mp4",
                        "size": 100,
                        "driver": {"name": "115 Open", "link_driver_name": ""},
                        "creator": {"id": 931, "name": "Lucifer"},
                        "tmdb_id": 95842,
                        "link": {"type": 300, "type_name": "云下载", "url": "ed2k://test"},
                        "cs_hash_id": 1246925,
                        "downloadable": True,
                        "download_request": {"type": 300, "contents": ["ed2k://test"], "csHashId": 1246925, "csCreator": "Lucifer"},
                    }
                ],
            }

        monkeypatch.setattr(CloudResourceManager, "search", fake_search)
        result = runner.invoke(
            main,
            [
                "--url",
                "http://localhost:8899",
                "--apikey",
                "secret-key",
                "--json",
                "cloud-resource",
                "search",
                "--keyword",
                "庆余年",
            ],
        )

        assert result.exit_code == 0
        payload = json.loads(result.output)
        assert payload["total"] == 1
        assert payload["list"][0]["download_request"]["type"] == 300

    def test_cloud_resource_search_command_human_output(self, monkeypatch):
        runner = CliRunner()
        monkeypatch.setattr(
            CloudResourceManager,
            "search",
            lambda self, **kwargs: {
                "total": 1,
                "pageNum": 1,
                "pageSize": 25,
                "list": [
                    {
                        "title": "庆余年.S01E46.mp4",
                        "size": 2251076541,
                        "driver": {"name": "115 Open"},
                        "creator": {"id": 931, "name": "Lucifer"},
                        "tmdb_id": 95842,
                        "link": {"type_name": "云下载"},
                        "cs_hash_id": 1246925,
                        "downloadable": True,
                    }
                ],
            },
        )

        result = runner.invoke(
            main,
            [
                "--url",
                "http://localhost:8899",
                "--apikey",
                "secret-key",
                "cloud-resource",
                "search",
                "--keyword",
                "庆余年",
            ],
        )

        assert result.exit_code == 0
        assert "Cloud Resource Search" in result.output
        assert "庆余年" in result.output

    def test_cloud_resource_download_command_json(self, monkeypatch):
        runner = CliRunner()

        def fake_submit_download(self, request, *, dir_path):
            assert request == {"type": 300, "contents": ["ed2k://test"], "csHashId": 1}
            assert dir_path == "/downloads"
            return {"status": "submitted", "type": 300, "dir": "/downloads", "count": 1, "response": True, "message": "SUCCESS"}

        monkeypatch.setattr(CloudResourceManager, "submit_download", fake_submit_download)
        result = runner.invoke(
            main,
            [
                "--url",
                "http://localhost:8899",
                "--apikey",
                "secret-key",
                "--json",
                "cloud-resource",
                "download",
                "--request",
                '{"type":300,"contents":["ed2k://test"],"csHashId":1}',
                "--dir",
                "/downloads",
            ],
        )

        assert result.exit_code == 0
        payload = json.loads(result.output)
        assert payload["status"] == "submitted"
        assert payload["count"] == 1

    def test_cloud_resource_download_rejects_invalid_json(self):
        runner = CliRunner()
        result = runner.invoke(
            main,
            [
                "--url",
                "http://localhost:8899",
                "--apikey",
                "secret-key",
                "cloud-resource",
                "download",
                "--request",
                "not-json",
            ],
        )

        assert result.exit_code != 0
        assert "--request must be valid JSON" in result.output

    def test_cloud_resource_rank_command_json(self, monkeypatch):
        runner = CliRunner()

        def fake_rank(self, *, range_type, stat_type, refresh):
            assert range_type == "today"
            assert stat_type == "count"
            assert refresh is True
            return {
                "range_type": "today",
                "stat_type": "count",
                "items": [
                    {
                        "rank": 1,
                        "creator_id": 931,
                        "creator": "小汐",
                        "count": 2030,
                        "size": 100,
                        "size_text": "100 B",
                        "value": 2030,
                        "value_text": "2030 次",
                    }
                ],
                "mine": {
                    "creator_id": 99,
                    "creator": "我",
                    "count": 5,
                    "size": 1,
                    "size_text": "1 B",
                    "rank": 20,
                    "surpass_percent": 39.39,
                    "value": 5,
                    "value_text": "5 次",
                },
            }

        monkeypatch.setattr(CloudResourceManager, "rank", fake_rank)
        result = runner.invoke(
            main,
            [
                "--url",
                "http://localhost:8899",
                "--apikey",
                "secret-key",
                "--json",
                "cloud-resource",
                "rank",
                "--range",
                "today",
                "--stat",
                "count",
                "--refresh",
            ],
        )

        assert result.exit_code == 0
        payload = json.loads(result.output)
        assert payload["items"][0]["creator"] == "小汐"
        assert payload["mine"]["rank"] == 20

    def test_cloud_resource_rank_command_human_output(self, monkeypatch):
        runner = CliRunner()
        monkeypatch.setattr(
            CloudResourceManager,
            "rank",
            lambda self, **kwargs: {
                "range_type": "today",
                "stat_type": "size",
                "items": [
                    {
                        "rank": 1,
                        "creator_id": 931,
                        "creator": "小汐",
                        "count": 2030,
                        "size": 1099511627776,
                        "size_text": "1.00 TB",
                        "value": 1099511627776,
                        "value_text": "1.00 TB",
                    }
                ],
                "mine": {
                    "creator": "我",
                    "rank": 20,
                    "value_text": "1.00 MB",
                    "surpass_percent": 39.39,
                },
            },
        )

        result = runner.invoke(
            main,
            [
                "--url",
                "http://localhost:8899",
                "--apikey",
                "secret-key",
                "cloud-resource",
                "rank",
                "--stat",
                "size",
            ],
        )

        assert result.exit_code == 0
        assert "Cloud Resource Rank" in result.output
        assert "小汐" in result.output
        assert "Mine" in result.output

    def test_media_rank_sources_json(self, monkeypatch):
        runner = CliRunner()

        monkeypatch.setattr(MediaManager, "rank_sources", lambda self: [{"value": 100, "text": "豆瓣"}])
        result = runner.invoke(
            main,
            [
                "--url",
                "http://localhost:8899",
                "--apikey",
                "secret-key",
                "--json",
                "media",
                "rank",
                "sources",
            ],
        )

        assert result.exit_code == 0
        payload = json.loads(result.output)
        assert payload[0]["value"] == 100
        assert payload[0]["text"] == "豆瓣"

    def test_media_rank_sources_human_output(self, monkeypatch):
        runner = CliRunner()

        monkeypatch.setattr(MediaManager, "rank_sources", lambda self: [{"value": 100, "text": "豆瓣"}])
        result = runner.invoke(
            main,
            [
                "--url",
                "http://localhost:8899",
                "--apikey",
                "secret-key",
                "media",
                "rank",
                "sources",
            ],
        )

        assert result.exit_code == 0
        assert "Media Rank Sources" in result.output
        assert "豆瓣" in result.output

    def test_media_rank_categories_json(self, monkeypatch):
        runner = CliRunner()

        def fake_rank_categories(self, media_source):
            assert media_source == MEDIA_RANK_SOURCE_MAP["douban"]
            return [{"code": "douban_tv", "name": "📺 电视榜单", "custom": False}]

        monkeypatch.setattr(MediaManager, "rank_categories", fake_rank_categories)
        result = runner.invoke(
            main,
            [
                "--url",
                "http://localhost:8899",
                "--apikey",
                "secret-key",
                "--json",
                "media",
                "rank",
                "categories",
                "--source",
                "douban",
            ],
        )

        assert result.exit_code == 0
        payload = json.loads(result.output)
        assert payload[0]["code"] == "douban_tv"

    def test_media_rank_subjects_json(self, monkeypatch):
        runner = CliRunner()

        def fake_rank_subjects(self, category_code):
            assert category_code == "douban_tv"
            return [{"code": "tv_domestic", "name": "热播国产剧", "custom": False, "landscape": False}]

        monkeypatch.setattr(MediaManager, "rank_subjects", fake_rank_subjects)
        result = runner.invoke(
            main,
            [
                "--url",
                "http://localhost:8899",
                "--apikey",
                "secret-key",
                "--json",
                "media",
                "rank",
                "subjects",
                "--category-code",
                "douban_tv",
            ],
        )

        assert result.exit_code == 0
        payload = json.loads(result.output)
        assert payload[0]["code"] == "tv_domestic"

    def test_media_rank_items_json(self, monkeypatch):
        runner = CliRunner()

        def fake_rank_items(self, category_code, code, page, page_size):
            assert category_code == "douban_tv"
            assert code == "tv_domestic"
            assert page == 1
            assert page_size == 25
            return {
                "total": 50,
                "pageNum": 1,
                "pageSize": 25,
                "list": [_normalized_media_item(title="危险关系", media_type="tv", year=2026, vote=7.9)],
            }

        monkeypatch.setattr(MediaManager, "rank_items", fake_rank_items)
        result = runner.invoke(
            main,
            [
                "--url",
                "http://localhost:8899",
                "--apikey",
                "secret-key",
                "--json",
                "media",
                "rank",
                "items",
                "--category-code",
                "douban_tv",
                "--code",
                "tv_domestic",
                "--page",
                "1",
                "--page-size",
                "25",
            ],
        )

        assert result.exit_code == 0
        payload = json.loads(result.output)
        assert payload["total"] == 50
        assert payload["list"][0]["title"] == "危险关系"
        assert payload["list"][0]["media_type"] == "tv"
        assert payload["list"][0]["poster_url"] == "https://example.test/poster.jpg"
        assert payload["list"][0]["subscription"] == {"subscribed": False, "id": None}
        assert payload["list"][0]["library"] == {"archived": True, "resource_count": 2}
        _assert_no_raw_media_noise(payload["list"][0])

    def test_media_rank_items_human_output(self, monkeypatch):
        runner = CliRunner()

        monkeypatch.setattr(
            MediaManager,
            "rank_items",
            lambda self, category_code, code, page, page_size: {
                "total": 50,
                "pageNum": 1,
                "pageSize": 25,
                "list": [
                    _normalized_media_item(
                        title="危险关系",
                        media_type="tv",
                        year=2026,
                        vote=7.9,
                        subscription={"subscribed": True, "id": 400},
                        library={"archived": False, "resource_count": 0},
                    )
                ],
            },
        )
        result = runner.invoke(
            main,
            [
                "--url",
                "http://localhost:8899",
                "--apikey",
                "secret-key",
                "media",
                "rank",
                "items",
                "--category-code",
                "douban_tv",
                "--code",
                "tv_domestic",
                "--page",
                "1",
                "--page-size",
                "25",
            ],
        )

        assert result.exit_code == 0
        assert "Media Rank Items" in result.output
        assert "危险关系" in result.output
        assert "Total" in result.output

    def test_media_rank_categories_requires_valid_source(self):
        runner = CliRunner()
        result = runner.invoke(
            main,
            [
                "--url",
                "http://localhost:8899",
                "--apikey",
                "secret-key",
                "media",
                "rank",
                "categories",
                "--source",
                "unknown",
            ],
        )

        assert result.exit_code != 0
        assert "Invalid value for '--source'" in result.output

    def test_media_rank_subjects_rejects_empty_category_code(self):
        runner = CliRunner()
        result = runner.invoke(
            main,
            [
                "--url",
                "http://localhost:8899",
                "--apikey",
                "secret-key",
                "media",
                "rank",
                "subjects",
                "--category-code",
                "   ",
            ],
        )

        assert result.exit_code != 0
        assert "--category-code cannot be empty" in result.output

    def test_media_rank_items_rejects_empty_code(self):
        runner = CliRunner()
        result = runner.invoke(
            main,
            [
                "--url",
                "http://localhost:8899",
                "--apikey",
                "secret-key",
                "media",
                "rank",
                "items",
                "--category-code",
                "douban_tv",
                "--code",
                "   ",
            ],
        )

        assert result.exit_code != 0
        assert "--code cannot be empty" in result.output

    def test_media_recommend_sources_json(self, monkeypatch):
        runner = CliRunner()

        monkeypatch.setattr(MediaManager, "recommend_sources", lambda self: [{"value": 100, "text": "豆瓣"}])
        result = runner.invoke(
            main,
            [
                "--url",
                "http://localhost:8899",
                "--apikey",
                "secret-key",
                "--json",
                "media",
                "recommend",
                "sources",
            ],
        )

        assert result.exit_code == 0
        payload = json.loads(result.output)
        assert payload[0]["value"] == 100

    def test_media_recommend_channels_json(self, monkeypatch):
        runner = CliRunner()

        def fake_recommend_channels(self, media_source):
            assert media_source == MEDIA_RECOMMEND_SOURCE_MAP["douban"]
            return [{"value": "movie", "text": "电影"}]

        monkeypatch.setattr(MediaManager, "recommend_channels", fake_recommend_channels)
        result = runner.invoke(
            main,
            [
                "--url",
                "http://localhost:8899",
                "--apikey",
                "secret-key",
                "--json",
                "media",
                "recommend",
                "channels",
                "--source",
                "douban",
            ],
        )

        assert result.exit_code == 0
        payload = json.loads(result.output)
        assert payload[0]["value"] == "movie"

    def test_media_recommend_options_json(self, monkeypatch):
        runner = CliRunner()

        def fake_recommend_options(self, media_source, channel):
            assert media_source == MEDIA_RECOMMEND_SOURCE_MAP["douban"]
            assert channel == "movie"
            return [{"id": "sort", "text": "排序", "options": [{"value": "", "text": "综合排序"}]}]

        monkeypatch.setattr(MediaManager, "recommend_options", fake_recommend_options)
        result = runner.invoke(
            main,
            [
                "--url",
                "http://localhost:8899",
                "--apikey",
                "secret-key",
                "--json",
                "media",
                "recommend",
                "options",
                "--source",
                "douban",
                "--channel",
                "movie",
            ],
        )

        assert result.exit_code == 0
        payload = json.loads(result.output)
        assert payload[0]["id"] == "sort"

    def test_media_recommend_items_json(self, monkeypatch):
        runner = CliRunner()

        def fake_recommend_items(self, media_source, channel, options, page, page_size):
            assert media_source == MEDIA_RECOMMEND_SOURCE_MAP["tmdb"]
            assert channel == "movie"
            assert options == {"sort": "", "year": "", "tag": "", "country": ""}
            assert page == 1
            assert page_size == 25
            return {
                "total": 50,
                "pageNum": 1,
                "pageSize": 25,
                "list": [_normalized_media_item(title="危险关系", media_type="tv", year=2026, vote=7.9)],
            }

        monkeypatch.setattr(MediaManager, "recommend_items", fake_recommend_items)
        result = runner.invoke(
            main,
            [
                "--url",
                "http://localhost:8899",
                "--apikey",
                "secret-key",
                "--json",
                "media",
                "recommend",
                "items",
                "--source",
                "tmdb",
                "--channel",
                "movie",
                "--options",
                '{"sort":"","year":"","tag":"","country":""}',
                "--page",
                "1",
                "--page-size",
                "25",
            ],
        )

        assert result.exit_code == 0
        payload = json.loads(result.output)
        assert payload["total"] == 50
        assert payload["list"][0]["media_type"] == "tv"
        assert payload["list"][0]["subscription"] == {"subscribed": False, "id": None}
        _assert_no_raw_media_noise(payload["list"][0])

    def test_media_recommend_options_human_output(self, monkeypatch):
        runner = CliRunner()

        monkeypatch.setattr(
            MediaManager,
            "recommend_options",
            lambda self, media_source, channel: [
                {"id": "sort", "text": "排序", "options": [{"value": "", "text": "综合排序"}]}
            ],
        )
        result = runner.invoke(
            main,
            [
                "--url",
                "http://localhost:8899",
                "--apikey",
                "secret-key",
                "media",
                "recommend",
                "options",
                "--source",
                "douban",
                "--channel",
                "movie",
            ],
        )

        assert result.exit_code == 0
        assert "Media Recommend Options" in result.output
        assert "排序" in result.output

    def test_media_recommend_items_human_output(self, monkeypatch):
        runner = CliRunner()

        monkeypatch.setattr(
            MediaManager,
            "recommend_items",
            lambda self, media_source, channel, options, page, page_size: {
                "total": 50,
                "pageNum": 1,
                "pageSize": 25,
                "list": [
                    _normalized_media_item(
                        title="危险关系",
                        media_type="tv",
                        year=2026,
                        vote=7.9,
                        subscription={"subscribed": True, "id": 400},
                        library={"archived": False, "resource_count": 0},
                    )
                ],
            },
        )
        result = runner.invoke(
            main,
            [
                "--url",
                "http://localhost:8899",
                "--apikey",
                "secret-key",
                "media",
                "recommend",
                "items",
                "--source",
                "douban",
                "--channel",
                "movie",
            ],
        )

        assert result.exit_code == 0
        assert "Media Recommend Items" in result.output
        assert "危险关系" in result.output

    def test_media_recommend_channels_requires_valid_source(self):
        runner = CliRunner()
        result = runner.invoke(
            main,
            [
                "--url",
                "http://localhost:8899",
                "--apikey",
                "secret-key",
                "media",
                "recommend",
                "channels",
                "--source",
                "unknown",
            ],
        )

        assert result.exit_code != 0
        assert "Invalid value for '--source'" in result.output

    def test_media_recommend_options_rejects_empty_channel(self):
        runner = CliRunner()
        result = runner.invoke(
            main,
            [
                "--url",
                "http://localhost:8899",
                "--apikey",
                "secret-key",
                "media",
                "recommend",
                "options",
                "--source",
                "douban",
                "--channel",
                "   ",
            ],
        )

        assert result.exit_code != 0
        assert "--channel cannot be empty" in result.output

    def test_media_recommend_items_rejects_invalid_options_json(self):
        runner = CliRunner()
        result = runner.invoke(
            main,
            [
                "--url",
                "http://localhost:8899",
                "--apikey",
                "secret-key",
                "media",
                "recommend",
                "items",
                "--source",
                "douban",
                "--channel",
                "movie",
                "--options",
                "{bad json}",
            ],
        )

        assert result.exit_code != 0
        assert "--options must be valid JSON" in result.output

    def test_media_recommend_items_rejects_non_object_options(self):
        runner = CliRunner()
        result = runner.invoke(
            main,
            [
                "--url",
                "http://localhost:8899",
                "--apikey",
                "secret-key",
                "media",
                "recommend",
                "items",
                "--source",
                "douban",
                "--channel",
                "movie",
                "--options",
                '[]',
            ],
        )

        assert result.exit_code != 0
        assert "--options must be a JSON object" in result.output

    def test_media_server_miss_episodes_check_json(self, monkeypatch):
        runner = CliRunner()

        def fake_miss_episodes_check(self):
            return {
                "total": 1,
                "items": [
                    {
                        "tmdbId": 139797,
                        "mediaType": "tv",
                        "title": "猎罪图鉴",
                        "year": 2022,
                        "episodes": [
                            {
                                "season": 1,
                                "totalEpisodes": 20,
                                "missEpisodes": [7],
                            }
                        ],
                    }
                ],
            }

        monkeypatch.setattr(MediaServerManager, "miss_episodes_check", fake_miss_episodes_check)
        result = runner.invoke(
            main,
            [
                "--url",
                "http://localhost:8899",
                "--apikey",
                "secret-key",
                "--json",
                "media-server",
                "miss-episodes-check",
            ],
        )

        assert result.exit_code == 0
        payload = json.loads(result.output)
        assert payload["total"] == 1
        assert payload["items"][0]["title"] == "猎罪图鉴"
        assert payload["items"][0]["episodes"][0]["missEpisodes"] == [7]

    def test_media_server_list_command_json(self, monkeypatch):
        runner = CliRunner()

        def fake_list(self):
            return {
                "total": 1,
                "items": [
                    {
                        "id": 1,
                        "name": "专线",
                        "type": 100,
                        "type_text": "Emby",
                        "enabled": True,
                        "default": True,
                        "updated_at_text": "2026-03-24 17:51:25",
                        "statistics": {
                            "movie_count": 11980,
                            "tv_count": 2880,
                            "time_seconds": 107.401,
                            "updated_at_text": "2026-04-26 00:01:47",
                        },
                    }
                ],
            }

        monkeypatch.setattr(MediaServerManager, "list", fake_list)
        result = runner.invoke(
            main,
            [
                "--url",
                "http://localhost:8899",
                "--apikey",
                "secret-key",
                "--json",
                "media-server",
                "list",
            ],
        )

        assert result.exit_code == 0
        payload = json.loads(result.output)
        assert payload["items"][0]["name"] == "专线"
        assert payload["items"][0]["statistics"]["movie_count"] == 11980

    def test_media_server_list_command_human_output(self, monkeypatch):
        runner = CliRunner()

        monkeypatch.setattr(
            MediaServerManager,
            "list",
            lambda self: {
                "total": 1,
                "items": [
                    {
                        "id": 1,
                        "name": "专线",
                        "type_text": "Emby",
                        "enabled": True,
                        "default": True,
                        "updated_at_text": "2026-03-24 17:51:25",
                        "statistics": {
                            "movie_count": 11980,
                            "tv_count": 2880,
                            "time_seconds": 107.401,
                            "updated_at_text": "2026-04-26 00:01:47",
                        },
                    }
                ],
            },
        )
        result = runner.invoke(
            main,
            [
                "--url",
                "http://localhost:8899",
                "--apikey",
                "secret-key",
                "media-server",
                "list",
            ],
        )

        assert result.exit_code == 0
        assert "Media Servers" in result.output
        assert "专线" in result.output
        assert "11980" in result.output

    def test_media_server_sync_items_command_json(self, monkeypatch):
        runner = CliRunner()

        def fake_sync_items(self, server_id, *, title, media_type, miss_eps, page, page_size):
            assert server_id == 1
            assert title == "猎罪"
            assert media_type == "tv"
            assert miss_eps is False
            assert page == 2
            assert page_size == 5
            return {
                "total": 1,
                "pageNum": 2,
                "pageSize": 5,
                "list": [{"title": "猎罪图鉴", "item_type": "tv", "miss_eps": False}],
            }

        monkeypatch.setattr(MediaServerManager, "sync_items", fake_sync_items)
        result = runner.invoke(
            main,
            [
                "--url",
                "http://localhost:8899",
                "--apikey",
                "secret-key",
                "--json",
                "media-server",
                "sync-items",
                "--id",
                "1",
                "--title",
                "猎罪",
                "--type",
                "tv",
                "--miss-eps",
                "false",
                "--page",
                "2",
                "--page-size",
                "5",
            ],
        )

        assert result.exit_code == 0
        payload = json.loads(result.output)
        assert payload["list"][0]["title"] == "猎罪图鉴"

    def test_media_server_sync_run_command_json(self, monkeypatch):
        runner = CliRunner()

        monkeypatch.setattr(
            MediaServerManager,
            "sync_run",
            lambda self, server_id: {"status": "submitted", "server_id": server_id, "response": True, "message": "SUCCESS"},
        )
        result = runner.invoke(
            main,
            [
                "--url",
                "http://localhost:8899",
                "--apikey",
                "secret-key",
                "--json",
                "media-server",
                "sync-run",
                "--id",
                "1",
            ],
        )

        assert result.exit_code == 0
        payload = json.loads(result.output)
        assert payload["status"] == "submitted"
        assert payload["server_id"] == 1

    def test_media_server_miss_episodes_check_human_output(self, monkeypatch):
        runner = CliRunner()

        def fake_miss_episodes_check(self):
            return {
                "total": 1,
                "items": [
                    {
                        "tmdbId": 68095,
                        "mediaType": "tv",
                        "title": "法医秦明",
                        "year": 2016,
                        "episodes": [
                            {
                                "season": 2,
                                "totalEpisodes": 18,
                                "missEpisodes": [5, 10, 12],
                            }
                        ],
                    }
                ],
            }

        monkeypatch.setattr(MediaServerManager, "miss_episodes_check", fake_miss_episodes_check)
        result = runner.invoke(
            main,
            [
                "--url",
                "http://localhost:8899",
                "--apikey",
                "secret-key",
                "media-server",
                "miss-episodes-check",
            ],
        )

        assert result.exit_code == 0
        assert "Miss Episodes Check" in result.output
        assert "Total: 1" in result.output
        assert "法医秦明 (2016)" in result.output
        assert "Season 2 / Total 18 / Missing: 5, 10, 12" in result.output

    def test_media_server_miss_episodes_check_empty_output(self, monkeypatch):
        runner = CliRunner()

        monkeypatch.setattr(MediaServerManager, "miss_episodes_check", lambda self: {"total": 0, "items": []})
        result = runner.invoke(
            main,
            [
                "--url",
                "http://localhost:8899",
                "--apikey",
                "secret-key",
                "media-server",
                "miss-episodes-check",
            ],
        )

        assert result.exit_code == 0
        assert "Total: 0" in result.output
        assert "✅ 无漏集" in result.output

    def test_media_server_miss_episodes_check_truncates_long_missing_list(self, monkeypatch):
        runner = CliRunner()

        def fake_miss_episodes_check(self):
            return {
                "total": 25,
                "items": [
                    {
                        "tmdbId": 69714,
                        "mediaType": "tv",
                        "title": "心理罪",
                        "year": 2015,
                        "episodes": [
                            {
                                "season": 1,
                                "totalEpisodes": 2110,
                                "missEpisodes": list(range(12, 40)),
                            }
                        ],
                    }
                ],
            }

        monkeypatch.setattr(MediaServerManager, "miss_episodes_check", fake_miss_episodes_check)
        result = runner.invoke(
            main,
            [
                "--url",
                "http://localhost:8899",
                "--apikey",
                "secret-key",
                "media-server",
                "miss-episodes-check",
            ],
        )

        assert result.exit_code == 0
        assert "Showing first 1 items" in result.output
        assert "... (28 total)" in result.output

    def test_media_server_miss_episodes_check_surfaces_backend_error(self, monkeypatch):
        runner = CliRunner()

        def fake_miss_episodes_check(self):
            raise ValueError("404 page not found")

        monkeypatch.setattr(MediaServerManager, "miss_episodes_check", fake_miss_episodes_check)
        result = runner.invoke(
            main,
            [
                "--url",
                "http://localhost:8899",
                "--apikey",
                "secret-key",
                "--json",
                "media-server",
                "miss-episodes-check",
            ],
        )

        assert result.exit_code != 0
        payload = json.loads(result.output)
        assert payload["error"] == "404 page not found"

    def test_site_list_command_json(self, monkeypatch):
        runner = CliRunner()

        def fake_list(self, *, name, enabled, switch_type):
            assert name == "馒头"
            assert enabled is True
            assert switch_type == "sign-in"
            return {
                "total": 1,
                "items": [
                    {
                        "id": 1,
                        "name": "馒头",
                        "code": "mteam",
                        "enabled": True,
                        "domain": "https://example.test",
                        "switches": {"sign_in": True},
                    }
                ],
            }

        monkeypatch.setattr(SiteManager, "list", fake_list)
        result = runner.invoke(
            main,
            [
                "--url",
                "http://localhost:8899",
                "--apikey",
                "secret-key",
                "--json",
                "site",
                "list",
                "--name",
                "馒头",
                "--enabled",
                "true",
                "--type",
                "sign-in",
            ],
        )

        assert result.exit_code == 0
        payload = json.loads(result.output)
        assert payload["items"][0]["name"] == "馒头"

    def test_site_data_latest_command_human_output(self, monkeypatch):
        runner = CliRunner()

        monkeypatch.setattr(
            SiteManager,
            "data_latest",
            lambda self, *, site_id, site_name, order_by, order_direction: {
                "total": 1,
                "items": [
                    {
                        "site_name": "馒头",
                        "is_login": True,
                        "signed_in": False,
                        "ratio": 2.5,
                        "uploaded_text": "1.00 TB",
                        "downloaded_text": "500.00 GB",
                        "bonus": 12345.6,
                        "seeding_count": 88,
                        "seeding_size_text": "2.00 TB",
                        "statistic_date": "2026-04-26",
                    }
                ],
            },
        )
        result = runner.invoke(
            main,
            [
                "--url",
                "http://localhost:8899",
                "--apikey",
                "secret-key",
                "site",
                "data",
                "latest",
            ],
        )

        assert result.exit_code == 0
        assert "Site Data Latest" in result.output
        assert "馒头" in result.output

    def test_site_sign_in_history_command_json(self, monkeypatch):
        runner = CliRunner()

        def fake_sign_in_history(self, *, site_name, page, page_size):
            assert site_name == "馒头"
            assert page == 2
            assert page_size == 5
            return {
                "total": 1,
                "pageNum": 2,
                "pageSize": 5,
                "list": [{"site_name": "馒头", "code": 100, "code_text": "签到成功"}],
            }

        monkeypatch.setattr(SiteManager, "sign_in_history", fake_sign_in_history)
        result = runner.invoke(
            main,
            [
                "--url",
                "http://localhost:8899",
                "--apikey",
                "secret-key",
                "--json",
                "site",
                "sign-in",
                "history",
                "--site-name",
                "馒头",
                "--page",
                "2",
                "--page-size",
                "5",
            ],
        )

        assert result.exit_code == 0
        payload = json.loads(result.output)
        assert payload["list"][0]["code_text"] == "签到成功"

    def test_site_sign_in_go_command_json(self, monkeypatch):
        runner = CliRunner()

        def fake_sign_in(self, *, site_ids):
            assert site_ids == [1, 2]
            return {"status": "submitted", "site_ids": site_ids, "all_enabled": False, "response": True, "message": "SUCCESS"}

        monkeypatch.setattr(SiteManager, "sign_in", fake_sign_in)
        result = runner.invoke(
            main,
            [
                "--url",
                "http://localhost:8899",
                "--apikey",
                "secret-key",
                "--json",
                "site",
                "sign-in",
                "go",
                "--id",
                "1",
                "--id",
                "2",
            ],
        )

        assert result.exit_code == 0
        payload = json.loads(result.output)
        assert payload["status"] == "submitted"
        assert payload["site_ids"] == [1, 2]

    def test_download_downloading_command_json(self, monkeypatch):
        runner = CliRunner()

        def fake_downloading(self, *, download_ids):
            assert download_ids == ["abc"]
            return {"total": 1, "items": [{"id": "abc", "title": "流浪地球", "progress_percent": 45.6}]}

        monkeypatch.setattr(DownloadManager, "downloading", fake_downloading)
        result = runner.invoke(
            main,
            [
                "--url",
                "http://localhost:8899",
                "--apikey",
                "secret-key",
                "--json",
                "download",
                "downloading",
                "--id",
                "abc",
            ],
        )

        assert result.exit_code == 0
        payload = json.loads(result.output)
        assert payload["items"][0]["id"] == "abc"

    def test_download_history_command_json(self, monkeypatch):
        runner = CliRunner()

        def fake_history(self, *, title, media_type, site_id, site_name, page, page_size):
            assert title == "庆余年"
            assert media_type == "tv"
            assert site_id == 2
            assert site_name == "馒头"
            assert page == 2
            assert page_size == 5
            return {"total": 1, "pageNum": 2, "pageSize": 5, "list": [{"id": 1, "title": "庆余年"}]}

        monkeypatch.setattr(DownloadManager, "history", fake_history)
        result = runner.invoke(
            main,
            [
                "--url",
                "http://localhost:8899",
                "--apikey",
                "secret-key",
                "--json",
                "download",
                "history",
                "--title",
                "庆余年",
                "--type",
                "tv",
                "--site-id",
                "2",
                "--site-name",
                "馒头",
                "--page",
                "2",
                "--page-size",
                "5",
            ],
        )

        assert result.exit_code == 0
        payload = json.loads(result.output)
        assert payload["list"][0]["title"] == "庆余年"

    def test_download_pause_resume_delete_commands_json(self, monkeypatch):
        runner = CliRunner()

        monkeypatch.setattr(DownloadManager, "pause", lambda self, download_id: {"status": "submitted", "action": "pause", "download_id": download_id})
        monkeypatch.setattr(DownloadManager, "resume", lambda self, download_id: {"status": "submitted", "action": "resume", "download_id": download_id})

        def fake_delete(self, download_id, *, delete_file):
            assert delete_file is True
            return {"status": "submitted", "action": "delete", "download_id": download_id}

        monkeypatch.setattr(DownloadManager, "delete", fake_delete)

        for command in ("pause", "resume"):
            result = runner.invoke(
                main,
                [
                    "--url",
                    "http://localhost:8899",
                    "--apikey",
                    "secret-key",
                    "--json",
                    "download",
                    command,
                    "--id",
                    "abc",
                ],
            )
            assert result.exit_code == 0
            assert json.loads(result.output)["action"] == command

        result = runner.invoke(
            main,
            [
                "--url",
                "http://localhost:8899",
                "--apikey",
                "secret-key",
                "--json",
                "download",
                "delete",
                "--id",
                "abc",
                "--delete-file",
            ],
        )
        assert result.exit_code == 0
        assert json.loads(result.output)["action"] == "delete"

    def test_downloaders_command_human_output(self, monkeypatch):
        runner = CliRunner()

        monkeypatch.setattr(
            DownloadManager,
            "downloaders",
            lambda self: {
                "total": 1,
                "items": [{"id": 1, "name": "qb", "type": 100, "enabled": True, "default": True, "url": "http://qb.test"}],
            },
        )
        result = runner.invoke(
            main,
            [
                "--url",
                "http://localhost:8899",
                "--apikey",
                "secret-key",
                "download",
                "downloaders",
            ],
        )

        assert result.exit_code == 0
        assert "Downloaders" in result.output
        assert "qb" in result.output

    def test_plugin_call_json(self, monkeypatch):
        runner = CliRunner()

        def fake_request(self, method, path, *, params=None, headers=None, json_body=None, timeout=30):
            assert method == "POST"
            assert path == "/api/v1/pluginsInstance/callByCode/zspace_service_assistant"
            assert json_body == {"action": "get_recent_state", "body": {}}
            return ApiResponse(
                status_code=200,
                ok=True,
                code=20000,
                message="SUCCESS",
                data={"message": "", "data": [{"basic": {"name": "Z4Pro"}}]},
                raw_body={},
                is_standard_response=True,
            )

        monkeypatch.setattr(MSClient, "request", fake_request)
        result = runner.invoke(
            main,
            [
                "--url",
                "http://localhost:8899",
                "--apikey",
                "secret-key",
                "--json",
                "plugin",
                "call",
                "--code",
                "zspace_service_assistant",
                "--body",
                '{"action":"get_recent_state","body":{}}',
            ],
        )

        assert result.exit_code == 0
        payload = json.loads(result.output)
        assert payload["message"] == ""
        assert payload["data"][0]["basic"]["name"] == "Z4Pro"

    def test_plugin_call_human_output_with_message_and_data(self, monkeypatch):
        runner = CliRunner()

        def fake_request(self, method, path, *, params=None, headers=None, json_body=None, timeout=30):
            return ApiResponse(
                status_code=200,
                ok=True,
                code=20000,
                message="SUCCESS",
                data={"message": "密钥生成成功", "data": {"value": 1}},
                raw_body={},
                is_standard_response=True,
            )

        monkeypatch.setattr(MSClient, "request", fake_request)
        result = runner.invoke(
            main,
            [
                "--url",
                "http://localhost:8899",
                "--apikey",
                "secret-key",
                "plugin",
                "call",
                "--code",
                "cloud_backup",
                "--body",
                '{"action":"genKey","body":{}}',
            ],
        )

        assert result.exit_code == 0
        assert "密钥生成成功" in result.output
        assert '"value": 1' in result.output

    def test_plugin_call_human_output_when_plugin_result_is_null(self, monkeypatch):
        runner = CliRunner()

        def fake_request(self, method, path, *, params=None, headers=None, json_body=None, timeout=30):
            return ApiResponse(
                status_code=200,
                ok=True,
                code=20000,
                message="SUCCESS",
                data=None,
                raw_body={},
                is_standard_response=True,
            )

        monkeypatch.setattr(MSClient, "request", fake_request)
        result = runner.invoke(
            main,
            [
                "--url",
                "http://localhost:8899",
                "--apikey",
                "secret-key",
                "plugin",
                "call",
                "--code",
                "moment",
                "--body",
                '{"action":"noop","body":{}}',
            ],
        )

        assert result.exit_code == 0
        assert "插件调用成功" in result.output

    def test_plugin_call_rejects_invalid_json(self):
        runner = CliRunner()
        result = runner.invoke(
            main,
            [
                "--url",
                "http://localhost:8899",
                "--apikey",
                "secret-key",
                "plugin",
                "call",
                "--code",
                "moment",
                "--body",
                "{bad json",
            ],
        )

        assert result.exit_code != 0
        assert "--body must be valid JSON" in result.output

    def test_plugin_call_rejects_non_object_body(self):
        runner = CliRunner()
        result = runner.invoke(
            main,
            [
                "--url",
                "http://localhost:8899",
                "--apikey",
                "secret-key",
                "plugin",
                "call",
                "--code",
                "moment",
                "--body",
                '["x"]',
            ],
        )

        assert result.exit_code != 0
        assert "--body must be a JSON object" in result.output

    def test_plugin_call_requires_action(self):
        runner = CliRunner()
        result = runner.invoke(
            main,
            [
                "--url",
                "http://localhost:8899",
                "--apikey",
                "secret-key",
                "plugin",
                "call",
                "--code",
                "moment",
                "--body",
                '{"body":{}}',
            ],
        )

        assert result.exit_code != 0
        assert "--body.action must be a non-empty string" in result.output

    def test_plugin_call_requires_object_body_field(self):
        runner = CliRunner()
        result = runner.invoke(
            main,
            [
                "--url",
                "http://localhost:8899",
                "--apikey",
                "secret-key",
                "plugin",
                "call",
                "--code",
                "moment",
                "--body",
                '{"action":"noop","body":"x"}',
            ],
        )

        assert result.exit_code != 0
        assert "--body.body must be a JSON object" in result.output

    def test_plugin_call_surfaces_backend_error(self, monkeypatch):
        runner = CliRunner()

        def fake_request(self, method, path, *, params=None, headers=None, json_body=None, timeout=30):
            return ApiResponse(
                status_code=200,
                ok=False,
                code=50000,
                message="还没有安装秘籍: 极空间服务助手",
                data=None,
                raw_body={},
                is_standard_response=True,
            )

        monkeypatch.setattr(MSClient, "request", fake_request)
        result = runner.invoke(
            main,
            [
                "--url",
                "http://localhost:8899",
                "--apikey",
                "secret-key",
                "--json",
                "plugin",
                "call",
                "--code",
                "zspace_service_assistant",
                "--body",
                '{"action":"get_recent_state","body":{}}',
            ],
        )

        assert result.exit_code != 0
        payload = json.loads(result.output)
        assert "还没有安装秘籍" in payload["error"]

    def test_subscribe_add_json(self, monkeypatch):
        runner = CliRunner()

        def fake_add(self, name, media_type, year, season):
            assert media_type == "movie"
            assert name == "Interstellar"
            assert year == 2014
            assert season is None
            return {
                "status": "ok",
                "subscribe": {
                    "name": name,
                    "type": media_type,
                    "year": year,
                },
            }

        monkeypatch.setattr(SubscribeManager, "add", fake_add)
        result = runner.invoke(
            main,
            [
                "--url",
                "http://localhost:8899",
                "--apikey",
                "secret-key",
                "--json",
                "subscribe",
                "add",
                "--type",
                "movie",
                "--name",
                "Interstellar",
                "--year",
                "2014",
            ],
        )

        assert result.exit_code == 0
        payload = json.loads(result.output)
        assert payload["status"] == "ok"
        assert payload["subscribe"]["name"] == "Interstellar"

    def test_subscribe_add_tv_defaults_season(self, monkeypatch):
        runner = CliRunner()

        def fake_add(self, name, media_type, year, season):
            assert media_type == "tv"
            assert season == 1
            return {
                "status": "ok",
                "subscribe": {
                    "name": name,
                    "type": media_type,
                    "year": year,
                    "season": season,
                },
            }

        monkeypatch.setattr(SubscribeManager, "add", fake_add)
        result = runner.invoke(
            main,
            [
                "--url",
                "http://localhost:8899",
                "--apikey",
                "secret-key",
                "subscribe",
                "add",
                "--type",
                "tv",
                "--name",
                "Breaking Bad",
                "--year",
                "2008",
            ],
        )

        assert result.exit_code == 0
        assert "season" in result.output
        assert "1" in result.output

    def test_subscribe_add_rejects_movie_season(self):
        runner = CliRunner()
        result = runner.invoke(
            main,
            [
                "--url",
                "http://localhost:8899",
                "--apikey",
                "secret-key",
                "subscribe",
                "add",
                "--type",
                "movie",
                "--name",
                "Interstellar",
                "--year",
                "2014",
                "--season",
                "1",
            ],
        )

        assert result.exit_code != 0
        assert "--season is only valid for tv subscriptions" in result.output

    def test_subscribe_add_rejects_empty_name(self):
        runner = CliRunner()
        result = runner.invoke(
            main,
            [
                "--url",
                "http://localhost:8899",
                "--apikey",
                "secret-key",
                "subscribe",
                "add",
                "--type",
                "movie",
                "--name",
                "   ",
                "--year",
                "2014",
            ],
        )

        assert result.exit_code != 0
        assert "--name cannot be empty" in result.output

    def test_subscribe_page_json(self, monkeypatch):
        runner = CliRunner()

        def fake_page(self, media_type, page, page_size):
            assert media_type == "movie"
            assert page == 1
            assert page_size == 99
            return {
                "total": 1,
                "pageNum": 1,
                "pageSize": 99,
                "list": [
                    {
                        "name": "Interstellar",
                        "type": "movie",
                        "year": 2014,
                        "status": 100,
                        "tmdbId": 157336,
                    }
                ],
            }

        monkeypatch.setattr(SubscribeManager, "page", fake_page)
        result = runner.invoke(
            main,
            [
                "--url",
                "http://localhost:8899",
                "--apikey",
                "secret-key",
                "--json",
                "subscribe",
                "page",
                "--type",
                "movie",
                "--page",
                "1",
                "--page-size",
                "99",
            ],
        )

        assert result.exit_code == 0
        payload = json.loads(result.output)
        assert payload["total"] == 1
        assert payload["list"][0]["name"] == "Interstellar"

    def test_subscribe_page_human_output(self, monkeypatch):
        runner = CliRunner()

        monkeypatch.setattr(
            SubscribeManager,
            "page",
            lambda self, media_type, page, page_size: {
                "total": 1,
                "pageNum": 1,
                "pageSize": 99,
                "list": [
                    {
                        "name": "Breaking Bad",
                        "type": "tv",
                        "year": 2008,
                        "season": 1,
                        "status": 200,
                        "tmdbId": 1396,
                    }
                ],
            },
        )
        result = runner.invoke(
            main,
            [
                "--url",
                "http://localhost:8899",
                "--apikey",
                "secret-key",
                "subscribe",
                "page",
                "--type",
                "tv",
                "--page",
                "1",
                "--page-size",
                "99",
            ],
        )

        assert result.exit_code == 0
        assert "Subscribe Page" in result.output
        assert "Type" in result.output
        assert "Breaking Bad" in result.output
        assert "订阅运行中" in result.output
