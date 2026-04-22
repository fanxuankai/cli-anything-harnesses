from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import click


@dataclass(frozen=True)
class ParamSpec:
    name: str
    target: str = "query"
    flags: tuple[str, ...] = ()
    wire_name: str | None = None
    click_type: Any = str
    required: bool = False
    multiple: bool = False
    is_flag: bool = False
    default: Any = None
    help: str = ""

    @property
    def key(self) -> str:
        return self.name.replace("-", "_")

    @property
    def field_name(self) -> str:
        return self.wire_name or self.name


@dataclass(frozen=True)
class CommandSpec:
    name: str
    method: str
    path: str
    args: tuple[ParamSpec, ...] = ()
    options: tuple[ParamSpec, ...] = ()
    body_mode: str = "none"
    response_mode: str = "json"
    unwrap_envelope: bool = True
    public: bool = False
    supports_output: bool = False
    timeout: int = 30
    allow_query_pairs: bool = True


@dataclass(frozen=True)
class GroupSpec:
    name: str
    help: str
    commands: tuple[CommandSpec, ...] = field(default_factory=tuple)
    existing_group: str | None = None


def arg(name: str, click_type: Any = str, wire_name: str | None = None) -> ParamSpec:
    return ParamSpec(name=name, target="path", click_type=click_type, wire_name=wire_name)


def qopt(
    name: str,
    *flags: str,
    wire_name: str | None = None,
    click_type: Any = str,
    required: bool = False,
    multiple: bool = False,
    is_flag: bool = False,
    default: Any = None,
    help: str = "",
) -> ParamSpec:
    return ParamSpec(
        name=name,
        target="query",
        flags=flags or (f"--{name}",),
        wire_name=wire_name,
        click_type=click_type,
        required=required,
        multiple=multiple,
        is_flag=is_flag,
        default=default,
        help=help,
    )


def bopt(
    name: str,
    *flags: str,
    wire_name: str | None = None,
    click_type: Any = str,
    required: bool = False,
    multiple: bool = False,
    is_flag: bool = False,
    default: Any = None,
    help: str = "",
) -> ParamSpec:
    return ParamSpec(
        name=name,
        target="body",
        flags=flags or (f"--{name}",),
        wire_name=wire_name,
        click_type=click_type,
        required=required,
        multiple=multiple,
        is_flag=is_flag,
        default=default,
        help=help,
    )


def fopt(name: str, *flags: str, wire_name: str | None = None, required: bool = True, help: str = "") -> ParamSpec:
    return ParamSpec(
        name=name,
        target="file",
        flags=flags or (f"--{name}",),
        wire_name=wire_name,
        click_type=click.Path(exists=True, dir_okay=False),
        required=required,
        help=help,
    )


PAGE_QUERY = (
    qopt("page-num", wire_name="pageNum", click_type=int),
    qopt("page-size", wire_name="pageSize", click_type=int),
)


def with_page(*options: ParamSpec) -> tuple[ParamSpec, ...]:
    return PAGE_QUERY + options


EXISTING_GROUP_SPECS: tuple[GroupSpec, ...] = (
    GroupSpec(
        name="system",
        existing_group="system",
        help="系统配置和系统状态。",
        commands=(
            CommandSpec("tmdb-languages", "GET", "/api/v1/system/tmdbLanguages"),
            CommandSpec("command-menus", "GET", "/api/v1/system/commandMenus"),
            CommandSpec(
                "gen-aes-key",
                "GET",
                "/api/v1/system/genAesKey",
                options=(qopt("key-length", wire_name="keyLength", click_type=int),),
            ),
            CommandSpec("flag", "GET", "/api/v1/system/flag"),
            CommandSpec("hash-report-statistic", "GET", "/api/v1/system/hashReportStatistic"),
            CommandSpec("hash-report-statistic-mine", "GET", "/api/v1/system/hashReportStatisticMine"),
            CommandSpec("upgrade-auto-update", "POST", "/api/v1/system/upgradeAutoUpdate", body_mode="json"),
            CommandSpec("path-link-search", "POST", "/api/v1/path/linkSearch", body_mode="json"),
            CommandSpec("path-link-delete", "DELETE", "/api/v1/path/linkDelete", body_mode="json"),
            CommandSpec(
                "upload",
                "POST",
                "/api/v1/system/upload",
                body_mode="multipart",
                options=(fopt("file", wire_name="file"),),
            ),
        ),
    ),
    GroupSpec(
        name="downloader",
        existing_group="downloader",
        help="下载器相关命令。",
        commands=(
            CommandSpec("save", "POST", "/api/v1/downloader/save", body_mode="json"),
            CommandSpec("delete", "DELETE", "/api/v1/downloader/delete/{id}", args=(arg("id", int),)),
            CommandSpec("set-default", "PUT", "/api/v1/downloader/default/{id}", args=(arg("id", int),)),
            CommandSpec("test", "POST", "/api/v1/downloader/test", body_mode="json"),
        ),
    ),
    GroupSpec(
        name="directory",
        existing_group="directory",
        help="目录与分类相关命令。",
        commands=(
            CommandSpec("save", "POST", "/api/v1/directory/save", body_mode="json"),
            CommandSpec("copy-from-tag", "POST", "/api/v1/directory/copyFromTag", body_mode="json"),
            CommandSpec("order", "PUT", "/api/v1/directory/order", body_mode="json"),
            CommandSpec("delete", "DELETE", "/api/v1/directory/delete/{id}", args=(arg("id", int),)),
        ),
    ),
    GroupSpec(
        name="site",
        existing_group="site",
        help="站点相关命令。",
        commands=(
            CommandSpec("save", "POST", "/api/v1/site/save", body_mode="json"),
            CommandSpec("delete", "DELETE", "/api/v1/site/delete/{id}", args=(arg("id", int),)),
            CommandSpec("page", "GET", "/api/v1/site/page", options=with_page(qopt("name"), qopt("enabled"), qopt("type", click_type=int))),
            CommandSpec("order", "PUT", "/api/v1/site/order", body_mode="json"),
            CommandSpec("switch", "PUT", "/api/v1/site/switch", body_mode="json"),
            CommandSpec("test", "GET", "/api/v1/site/test", options=(qopt("id", click_type=int), qopt("type", click_type=int))),
            CommandSpec("update-configs", "GET", "/api/v1/site/updateConfigs"),
            CommandSpec("meta", "GET", "/api/v1/site/meta/{id}", args=(arg("id", int),)),
            CommandSpec("batch-update", "PUT", "/api/v1/site/batchUpdate", body_mode="json"),
            CommandSpec("batch-update-all-inactive-day", "PUT", "/api/v1/site/batchUpdateAllInactiveDay", body_mode="json"),
            CommandSpec("backup", "GET", "/api/v1/site/backup"),
            CommandSpec("recovery", "GET", "/api/v1/site/recovery"),
        ),
    ),
    GroupSpec(
        name="media",
        existing_group="media",
        help="媒体搜索相关命令。",
        commands=(
            CommandSpec("detail", "POST", "/api/v1/media/detail", body_mode="json"),
            CommandSpec("douban-details", "POST", "/api/v1/media/doubanDetails", body_mode="json"),
            CommandSpec("season-episodes", "GET", "/api/v1/media/seasonEpisodes"),
            CommandSpec("refresh-media-server", "POST", "/api/v1/media/refreshMediaServer", body_mode="json"),
            CommandSpec("delete-tmdb-cache", "DELETE", "/api/v1/media/deleteTmdbCache", body_mode="json"),
            CommandSpec("count-cs-hash-torrents", "GET", "/api/v1/media/countCsHashTorrents"),
        ),
    ),
)


NEW_GROUP_SPECS: tuple[GroupSpec, ...] = (
    GroupSpec(
        "user",
        "用户与管理员管理。",
        commands=(
            CommandSpec("register", "POST", "/api/v1/user/register", body_mode="json", public=True),
            CommandSpec("init-admin-status", "GET", "/api/v1/user/initAdminStatus", public=True),
            CommandSpec("info", "GET", "/api/v1/user/info"),
            CommandSpec("logout", "POST", "/api/v1/user/logout"),
            CommandSpec("logout-by-tokens", "POST", "/api/v1/user/logoutByTokens", body_mode="json"),
            CommandSpec("tokens", "GET", "/api/v1/user/tokens"),
            CommandSpec("update-avatar", "PUT", "/api/v1/user/updateAvatar", body_mode="json"),
            CommandSpec(
                "upload-avatar",
                "POST",
                "/api/v1/user/uploadAvatar",
                body_mode="multipart",
                options=(fopt("file", wire_name="file"),),
            ),
            CommandSpec("update-base-info", "PUT", "/api/v1/user/updateBaseInfo", body_mode="json"),
            CommandSpec("update-password", "PUT", "/api/v1/user/updatePassword", body_mode="json"),
            CommandSpec("update-dashboard-modules", "POST", "/api/v1/user/updateDashboardModules", body_mode="json"),
            CommandSpec("page", "POST", "/api/v1/user/page", body_mode="json"),
            CommandSpec("save", "POST", "/api/v1/user/save", body_mode="json"),
            CommandSpec("delete", "DELETE", "/api/v1/user/delete/{user_id}", args=(arg("user_id", int, "userId"),)),
        ),
    ),
    GroupSpec(
        "network-ping",
        "网络探测相关命令。",
        commands=(
            CommandSpec("list", "GET", "/api/v1/newworkPing/list"),
            CommandSpec("ping", "POST", "/api/v1/newworkPing/ping", body_mode="json"),
        ),
    ),
    GroupSpec(
        "user-api-key",
        "用户 API Key 管理。",
        commands=(
            CommandSpec("list", "GET", "/api/v1/userApiKey/list"),
            CommandSpec("switch", "POST", "/api/v1/userApiKey/switch", body_mode="json"),
            CommandSpec("add", "POST", "/api/v1/userApiKey/add", body_mode="json"),
            CommandSpec("delete", "DELETE", "/api/v1/userApiKey/delete/{api_key_id}", args=(arg("api_key_id", int, "apiKeyId"),)),
        ),
    ),
    GroupSpec("dict", "字典选项。", commands=(CommandSpec("options", "GET", "/api/v1/dict/options"),)),
    GroupSpec(
        "system-message",
        "系统消息管理。",
        commands=(
            CommandSpec("page", "GET", "/api/v1/systemMessage/page", options=with_page()),
            CommandSpec("delete", "DELETE", "/api/v1/systemMessage/delete", body_mode="json"),
            CommandSpec("clear", "DELETE", "/api/v1/systemMessage/clear"),
        ),
    ),
    GroupSpec(
        "dynamic-form",
        "动态表单。",
        commands=(CommandSpec("detail", "GET", "/api/v1/dynamicForm/detail", options=(qopt("group"), qopt("code"))),),
    ),
    GroupSpec(
        "logs",
        "系统日志。",
        commands=(
            CommandSpec("page", "POST", "/api/v1/logs/page", body_mode="json"),
            CommandSpec("clear", "DELETE", "/api/v1/logs/clear"),
        ),
    ),
    GroupSpec(
        "plugins",
        "插件定义管理。",
        commands=(
            CommandSpec("list", "GET", "/api/v1/plugins/list"),
            CommandSpec("favorite", "POST", "/api/v1/plugins/favorite/{code}", args=(arg("code"),)),
            CommandSpec("un-favorite", "DELETE", "/api/v1/plugins/unFavorite/{code}", args=(arg("code"),)),
        ),
    ),
    GroupSpec(
        "plugins-instance",
        "插件实例管理。",
        commands=(
            CommandSpec("save", "POST", "/api/v1/pluginsInstance/save", body_mode="json"),
            CommandSpec("list", "GET", "/api/v1/pluginsInstance/list"),
            CommandSpec("detail", "GET", "/api/v1/pluginsInstance/detail/{id}", args=(arg("id", int),)),
            CommandSpec("delete", "DELETE", "/api/v1/pluginsInstance/delete/{id}", args=(arg("id", int),)),
            CommandSpec("call", "POST", "/api/v1/pluginsInstance/call/{id}", args=(arg("id", int),), body_mode="json"),
            CommandSpec("call-by-code", "POST", "/api/v1/pluginsInstance/callByCode/{code}", args=(arg("code"),), body_mode="json"),
        ),
    ),
    GroupSpec(
        "system-tools",
        "系统工具。",
        commands=(CommandSpec("clear-scrape-dir", "DELETE", "/api/v1/systemTools/clearScrapeDir", body_mode="json"),),
    ),
    GroupSpec(
        "site-data",
        "站点统计数据。",
        commands=(
            CommandSpec("sync", "POST", "/api/v1/siteData/sync", body_mode="json"),
            CommandSpec("total", "GET", "/api/v1/siteData/total"),
            CommandSpec("history", "POST", "/api/v1/siteData/history", body_mode="json"),
            CommandSpec("latest", "GET", "/api/v1/siteData/latest", options=(qopt("site-id", wire_name="siteId", click_type=int), qopt("site-name", wire_name="siteName"), qopt("order-by", wire_name="orderBy"), qopt("order-direction", wire_name="orderDirection"))),
        ),
    ),
    GroupSpec(
        "site-notice",
        "站点公告。",
        commands=(
            CommandSpec("sync", "POST", "/api/v1/siteNotice/sync", body_mode="json"),
            CommandSpec("page", "GET", "/api/v1/siteNotice/page", options=with_page(qopt("site-name", wire_name="siteName"))),
        ),
    ),
    GroupSpec(
        "site-message",
        "站点消息。",
        commands=(
            CommandSpec("sync", "POST", "/api/v1/siteMessage/sync", body_mode="json"),
            CommandSpec("page", "GET", "/api/v1/siteMessage/page", options=with_page(qopt("site-name", wire_name="siteName"), qopt("read"))),
            CommandSpec("mark-as-read", "PUT", "/api/v1/siteMessage/markAsRead", body_mode="json"),
        ),
    ),
    GroupSpec(
        "site-resource",
        "站点资源搜索。",
        commands=(
            CommandSpec("search-box", "GET", "/api/v1/siteResource/searchBox/{site_id}", args=(arg("site_id", int, "siteId"),)),
            CommandSpec("cate-options", "GET", "/api/v1/siteResource/cateOptions/{site_id}", args=(arg("site_id", int, "siteId"),)),
            CommandSpec("page", "POST", "/api/v1/siteResource/page", body_mode="json"),
        ),
    ),
    GroupSpec(
        "site-sign-in",
        "站点签到。",
        commands=(
            CommandSpec("go", "POST", "/api/v1/siteSignIn/go", body_mode="json"),
            CommandSpec("page", "GET", "/api/v1/siteSignIn/page", options=with_page()),
        ),
    ),
    GroupSpec(
        "site-request-history",
        "站点请求历史。",
        commands=(
            CommandSpec("page", "GET", "/api/v1/siteRequestHistory/page", options=with_page()),
            CommandSpec("request-id-options", "GET", "/api/v1/siteRequestHistory/requestIdOptions"),
            CommandSpec("detail", "GET", "/api/v1/siteRequestHistory/detail/{id}", args=(arg("id", int),)),
            CommandSpec("delete", "DELETE", "/api/v1/siteRequestHistory/delete", body_mode="json"),
        ),
    ),
    GroupSpec(
        "download-params",
        "下载参数配置。",
        commands=(
            CommandSpec("list", "GET", "/api/v1/downloadParams/list"),
            CommandSpec("save", "POST", "/api/v1/downloadParams/save", body_mode="json"),
            CommandSpec("detail", "GET", "/api/v1/downloadParams/detail/{id}", args=(arg("id", int),)),
            CommandSpec("delete", "DELETE", "/api/v1/downloadParams/delete/{id}", args=(arg("id", int),)),
            CommandSpec("set-default", "PUT", "/api/v1/downloadParams/default/{id}", args=(arg("id", int),)),
        ),
    ),
    GroupSpec(
        "download",
        "下载流程命令。",
        commands=(
            CommandSpec("torrents", "POST", "/api/v1/download/torrents", body_mode="json"),
            CommandSpec("enclosures", "POST", "/api/v1/download/enclosures", body_mode="json"),
            CommandSpec("site-resource", "POST", "/api/v1/download/siteResource", body_mode="json"),
            CommandSpec("media-torrent", "POST", "/api/v1/download/mediaTorrent", body_mode="json"),
            CommandSpec("details-url", "POST", "/api/v1/download/detailsUrl", body_mode="json"),
            CommandSpec("downloading", "POST", "/api/v1/download/downloading", body_mode="json"),
            CommandSpec("resume", "GET", "/api/v1/download/resume/{id}", args=(arg("id"),)),
            CommandSpec("pause", "GET", "/api/v1/download/pause/{id}", args=(arg("id"),)),
            CommandSpec("delete", "DELETE", "/api/v1/download/delete/{id}", args=(arg("id"),)),
            CommandSpec("history", "GET", "/api/v1/download/history", options=with_page(qopt("title"), qopt("media-type", wire_name="mediaType"), qopt("site-id", wire_name="siteId", click_type=int), qopt("site-name", wire_name="siteName"))),
            CommandSpec("clear-history", "POST", "/api/v1/download/clearHistory"),
        ),
    ),
    GroupSpec(
        "directory-category",
        "目录分类管理。",
        commands=(
            CommandSpec("list", "GET", "/api/v1/directoryCategory/list"),
            CommandSpec("save", "POST", "/api/v1/directoryCategory/save", body_mode="json"),
            CommandSpec("order", "PUT", "/api/v1/directoryCategory/order", body_mode="json"),
            CommandSpec("delete", "DELETE", "/api/v1/directoryCategory/delete/{id}", args=(arg("id", int),)),
            CommandSpec("generate-defaults", "GET", "/api/v1/directoryCategory/generateDefaults"),
        ),
    ),
    GroupSpec(
        "directory-subcategory",
        "目录子分类管理。",
        commands=(
            CommandSpec("options", "GET", "/api/v1/directorySubCategory/options"),
            CommandSpec("list", "GET", "/api/v1/directorySubCategory/list", options=(qopt("category-id", wire_name="categoryId", click_type=int),)),
            CommandSpec("save", "POST", "/api/v1/directorySubCategory/save", body_mode="json"),
            CommandSpec("order", "PUT", "/api/v1/directorySubCategory/order", body_mode="json"),
            CommandSpec("delete", "DELETE", "/api/v1/directorySubCategory/delete/{id}", args=(arg("id", int),)),
        ),
    ),
    GroupSpec(
        "cloud-storage",
        "云存储与挂载管理。",
        commands=(
            CommandSpec("list", "GET", "/api/v1/cloudStorage/list"),
            CommandSpec("page", "GET", "/api/v1/cloudStorage/page", options=with_page(qopt("driver"), qopt("mount-path", wire_name="mountPath"), qopt("show-disabled", wire_name="showDisabled"))),
            CommandSpec("mount-paths", "GET", "/api/v1/cloudStorage/mountPaths"),
            CommandSpec("enable", "POST", "/api/v1/cloudStorage/enable", body_mode="json"),
            CommandSpec("disable", "POST", "/api/v1/cloudStorage/disable", body_mode="json"),
            CommandSpec("save", "POST", "/api/v1/cloudStorage/save", body_mode="json"),
            CommandSpec("get", "GET", "/api/v1/cloudStorage/get", options=(qopt("id", click_type=int),)),
            CommandSpec("delete", "POST", "/api/v1/cloudStorage/delete", body_mode="json"),
            CommandSpec("force-delete", "DELETE", "/api/v1/cloudStorage/forceDelete", body_mode="json"),
            CommandSpec("load-all", "POST", "/api/v1/cloudStorage/loadAll"),
            CommandSpec("strm302", "GET", "/api/v1/cloudStorage/strm302", options=(qopt("path"), qopt("pick-code", wire_name="pickCode"), qopt("local-proxy", wire_name="localProxy"), qopt("proxy-download", wire_name="proxyDownload")), response_mode="content", supports_output=True, unwrap_envelope=False),
        ),
    ),
    GroupSpec(
        "cloud-storage-driver",
        "云存储驱动。",
        commands=(
            CommandSpec("list", "GET", "/api/v1/cloudStorageDriver/list"),
            CommandSpec("names", "GET", "/api/v1/cloudStorageDriver/names"),
            CommandSpec("info", "GET", "/api/v1/cloudStorageDriver/info", options=(qopt("driver"),)),
        ),
    ),
    GroupSpec(
        "cloud-storage-fs",
        "云存储文件系统操作。",
        commands=(
            CommandSpec("mkdir", "POST", "/api/v1/cloudStorageFs/mkdir", body_mode="json"),
            CommandSpec("rename", "POST", "/api/v1/cloudStorageFs/rename", body_mode="json"),
            CommandSpec("list", "POST", "/api/v1/cloudStorageFs/list", body_mode="json"),
            CommandSpec("get", "POST", "/api/v1/cloudStorageFs/get", body_mode="json"),
            CommandSpec("move", "POST", "/api/v1/cloudStorageFs/move", body_mode="json"),
            CommandSpec("copy", "POST", "/api/v1/cloudStorageFs/copy", body_mode="json"),
            CommandSpec("remove", "POST", "/api/v1/cloudStorageFs/remove", body_mode="json"),
            CommandSpec("remove-empty-directory", "POST", "/api/v1/cloudStorageFs/remove_empty_directory", body_mode="json"),
            CommandSpec("transfer", "POST", "/api/v1/cloudStorageFs/transfer", body_mode="json"),
            CommandSpec("upload", "POST", "/api/v1/cloudStorageFs/upload", body_mode="json"),
            CommandSpec("list-upload-dir", "POST", "/api/v1/cloudStorageFs/listUploadDir", body_mode="json"),
            CommandSpec("share-snap", "POST", "/api/v1/cloudStorageFs/shareSnap", body_mode="json"),
            CommandSpec("share-receive", "POST", "/api/v1/cloudStorageFs/shareReceive", body_mode="json"),
        ),
    ),
    GroupSpec(
        "cloud-storage-task",
        "云存储任务管理。",
        commands=(
            CommandSpec("info", "POST", "/api/v1/cloudStorageTask/info", body_mode="json"),
            CommandSpec("done", "GET", "/api/v1/cloudStorageTask/done", options=with_page(qopt("type"))),
            CommandSpec("undone", "GET", "/api/v1/cloudStorageTask/undone", options=with_page(qopt("type"))),
            CommandSpec("delete", "POST", "/api/v1/cloudStorageTask/delete", body_mode="json"),
            CommandSpec("cancel", "POST", "/api/v1/cloudStorageTask/cancel", body_mode="json"),
            CommandSpec("clear-done", "POST", "/api/v1/cloudStorageTask/clear_done", body_mode="json"),
            CommandSpec("clear-succeeded", "POST", "/api/v1/cloudStorageTask/clear_succeeded", body_mode="json"),
            CommandSpec("retry", "POST", "/api/v1/cloudStorageTask/retry", body_mode="json"),
            CommandSpec("retry-failed", "POST", "/api/v1/cloudStorageTask/retry_failed", body_mode="json"),
            CommandSpec("delete-some", "POST", "/api/v1/cloudStorageTask/delete_some", body_mode="json"),
            CommandSpec("cancel-some", "POST", "/api/v1/cloudStorageTask/cancel_some", body_mode="json"),
            CommandSpec("retry-some", "POST", "/api/v1/cloudStorageTask/retry_some", body_mode="json"),
            CommandSpec("off-only-fast-upload", "POST", "/api/v1/cloudStorageTask/offOnlyFastUpload", body_mode="json"),
        ),
    ),
    GroupSpec(
        "cloud-storage-transfer",
        "云存储整理规则。",
        commands=(
            CommandSpec("list", "GET", "/api/v1/cloudStorageTransfer/list"),
            CommandSpec("save", "POST", "/api/v1/cloudStorageTransfer/save", body_mode="json"),
            CommandSpec("delete", "DELETE", "/api/v1/cloudStorageTransfer/delete/{id}", args=(arg("id", int),)),
            CommandSpec("run", "POST", "/api/v1/cloudStorageTransfer/run/{id}", args=(arg("id", int),), body_mode="json"),
        ),
    ),
    GroupSpec(
        "generate-strm",
        "STRM 生成规则。",
        commands=(
            CommandSpec("list", "GET", "/api/v1/generateStrm/list"),
            CommandSpec("save", "POST", "/api/v1/generateStrm/save", body_mode="json"),
            CommandSpec("delete", "DELETE", "/api/v1/generateStrm/delete/{id}", args=(arg("id", int),)),
            CommandSpec("run", "POST", "/api/v1/generateStrm/run/{id}", args=(arg("id", int),), body_mode="json"),
            CommandSpec("fix-strm", "PUT", "/api/v1/generateStrm/fixStrm", body_mode="json"),
        ),
    ),
    GroupSpec(
        "open115",
        "115 开放接口登录。",
        commands=(
            CommandSpec("qrcode", "GET", "/api/v1/open115/qrcode"),
            CommandSpec("qrcode-status", "POST", "/api/v1/open115/qrcodeStatus", body_mode="json"),
            CommandSpec("code-to-token", "POST", "/api/v1/open115/codeToToken", body_mode="json"),
        ),
    ),
    GroupSpec("u115", "115 批量建库。", commands=(CommandSpec("batch-create-115-share-storages", "POST", "/api/v1/u115/batchCreate115ShareStorages", body_mode="json"),)),
    GroupSpec("open123", "Open123 接口。", commands=(CommandSpec("generate-share", "POST", "/api/v1/open123/generateShare", body_mode="json", timeout=300),)),
    GroupSpec(
        "proxy115",
        "115 代理接口。",
        commands=(
            CommandSpec("qrcode-token", "POST", "/api/v1/proxy115/qrcode_token", body_mode="json"),
            CommandSpec("qrcode-status", "POST", "/api/v1/proxy115/qrcode_status", body_mode="json"),
            CommandSpec("qrcode-result", "POST", "/api/v1/proxy115/qrcode_result", body_mode="json"),
        ),
    ),
    GroupSpec(
        "torrent",
        "种子分析与下载链接。",
        commands=(
            CommandSpec("download-url", "GET", "/api/v1/torrent/downloadUrl/{id}", args=(arg("id", int),)),
            CommandSpec("analysis", "POST", "/api/v1/torrent/analysis", body_mode="json"),
        ),
    ),
    GroupSpec(
        "torrent-search",
        "种子搜索。",
        commands=(
            CommandSpec("media", "POST", "/api/v1/torrentSearch/media", body_mode="json"),
            CommandSpec("cloud-storage", "POST", "/api/v1/torrentSearch/cloudStorage", body_mode="json"),
            CommandSpec("site", "POST", "/api/v1/torrentSearch/site", body_mode="json"),
            CommandSpec("cloud-storage-keyword", "POST", "/api/v1/torrentSearch/cloudStorageKeyword", body_mode="json"),
            CommandSpec("options", "GET", "/api/v1/torrentSearch/options"),
            CommandSpec("page", "POST", "/api/v1/torrentSearch/page", body_mode="json"),
        ),
    ),
    GroupSpec(
        "torrent-search-task",
        "种子搜索任务。",
        commands=(
            CommandSpec("page", "GET", "/api/v1/torrentSearchTask/page", options=with_page()),
            CommandSpec("detail", "GET", "/api/v1/torrentSearchTask/detail/{id}", args=(arg("id", int),)),
            CommandSpec("delete", "DELETE", "/api/v1/torrentSearchTask/delete", body_mode="json"),
            CommandSpec("hot-keywords", "GET", "/api/v1/torrentSearchTask/hotKeywords"),
            CommandSpec("recommend", "GET", "/api/v1/torrentSearchTask/recommend/{id}", args=(arg("id", int),)),
            CommandSpec("reorder", "PUT", "/api/v1/torrentSearchTask/reorder/{id}", args=(arg("id", int),), timeout=300),
        ),
    ),
    GroupSpec(
        "torrent-search-history",
        "种子搜索历史。",
        commands=(CommandSpec("list", "GET", "/api/v1/torrentSearchHistory/list", options=with_page()),),
    ),
    GroupSpec(
        "torrent-match",
        "种子匹配规则。",
        commands=(
            CommandSpec("options", "GET", "/api/v1/torrentMatch/options"),
            CommandSpec("save", "POST", "/api/v1/torrentMatch/save", body_mode="json"),
            CommandSpec("list", "GET", "/api/v1/torrentMatch/list"),
            CommandSpec("detail", "GET", "/api/v1/torrentMatch/detail/{id}", args=(arg("id", int),)),
            CommandSpec("delete", "DELETE", "/api/v1/torrentMatch/delete/{id}", args=(arg("id", int),)),
            CommandSpec("copy", "POST", "/api/v1/torrentMatch/copy/{id}", args=(arg("id", int),)),
        ),
    ),
    GroupSpec(
        "torrent-sort",
        "种子排序规则。",
        commands=(
            CommandSpec("save", "POST", "/api/v1/torrentSort/save", body_mode="json"),
            CommandSpec("list", "GET", "/api/v1/torrentSort/list"),
            CommandSpec("detail", "GET", "/api/v1/torrentSort/detail/{id}", args=(arg("id", int),)),
            CommandSpec("delete", "DELETE", "/api/v1/torrentSort/delete/{id}", args=(arg("id", int),)),
        ),
    ),
    GroupSpec(
        "subscribe",
        "订阅管理。",
        commands=(
            CommandSpec("page", "GET", "/api/v1/subscribe/page", options=with_page()),
            CommandSpec("save", "POST", "/api/v1/subscribe/save", body_mode="json"),
            CommandSpec("detail", "GET", "/api/v1/subscribe/detail/{id}", args=(arg("id", int),)),
            CommandSpec("delete", "DELETE", "/api/v1/subscribe/delete/{id}", args=(arg("id", int),)),
            CommandSpec("refresh", "POST", "/api/v1/subscribe/refresh/{id}", args=(arg("id", int),)),
            CommandSpec("refresh-all", "POST", "/api/v1/subscribe/refreshAll"),
            CommandSpec("search", "POST", "/api/v1/subscribe/search/{id}", args=(arg("id", int),)),
            CommandSpec("rss", "POST", "/api/v1/subscribe/rss/{id}", args=(arg("id", int),)),
            CommandSpec("resubscribe", "POST", "/api/v1/subscribe/resubscribe", body_mode="json"),
            CommandSpec("resubscribe-all", "POST", "/api/v1/subscribe/resubscribeAll"),
        ),
    ),
    GroupSpec(
        "subscribe-default-config",
        "订阅默认配置。",
        commands=(
            CommandSpec("save", "POST", "/api/v1/subscribeDefaultConfig/save", body_mode="json"),
            CommandSpec("detail", "GET", "/api/v1/subscribeDefaultConfig/detail/{type}", args=(arg("type"),)),
            CommandSpec("delete", "DELETE", "/api/v1/subscribeDefaultConfig/delete/{type}", args=(arg("type"),)),
        ),
    ),
    GroupSpec(
        "subscribe-calendar",
        "订阅日历。",
        commands=(CommandSpec("list", "GET", "/api/v1/subscribeCalendar/list"),),
    ),
    GroupSpec(
        "message",
        "消息发送。",
        commands=(
            CommandSpec("send", "POST", "/api/v1/message/send", body_mode="json", timeout=900),
            CommandSpec("open-send", "POST", "/api/v1/message/openSend", body_mode="json", timeout=900),
            CommandSpec("interactive", "POST", "/api/v1/message/interactive", body_mode="json", timeout=900),
        ),
    ),
    GroupSpec(
        "message-channel",
        "消息渠道。",
        commands=(
            CommandSpec("list", "GET", "/api/v1/messageChannel/list"),
            CommandSpec("save", "POST", "/api/v1/messageChannel/save", body_mode="json"),
            CommandSpec("detail", "GET", "/api/v1/messageChannel/detail/{id}", args=(arg("id", int),)),
            CommandSpec("delete", "DELETE", "/api/v1/messageChannel/delete/{id}", args=(arg("id", int),)),
            CommandSpec("push-types", "GET", "/api/v1/messageChannel/pushTypes"),
            CommandSpec("plugin-switches", "GET", "/api/v1/messageChannel/pluginSwitches"),
            CommandSpec("types", "GET", "/api/v1/messageChannel/types"),
            CommandSpec("test", "POST", "/api/v1/messageChannel/test", body_mode="json"),
        ),
    ),
    GroupSpec(
        "message-wechat",
        "企业微信消息渠道。",
        commands=(
            CommandSpec("create-menu", "GET", "/api/v1/messageWechat/createMenu/{id}", args=(arg("id", int),)),
            CommandSpec("gen-receive-url", "GET", "/api/v1/messageWechat/genReceiveUrl/{id}", args=(arg("id", int),)),
        ),
    ),
    GroupSpec(
        "service-ocr",
        "OCR 服务。",
        commands=(
            CommandSpec("test", "POST", "/api/v1/service/ocr/test", body_mode="json"),
            CommandSpec("captcha-ocr", "POST", "/api/v1/service/ocr/captchaOcr", body_mode="json"),
        ),
    ),
    GroupSpec(
        "pansou",
        "盘搜搜索。",
        commands=(CommandSpec("search", "GET", "/api/v1/pansou/search", options=with_page(qopt("keyword", required=True))),),
    ),
    GroupSpec(
        "hdhive",
        "HDHive 资源。",
        commands=(
            CommandSpec("resources", "GET", "/api/v1/hdhive/resources", options=with_page(qopt("tmdb-id", wire_name="tmdbId", click_type=int, required=True), qopt("media-type", wire_name="mediaType", required=True))),
            CommandSpec("unlock", "POST", "/api/v1/hdhive/unlock", body_mode="json"),
        ),
    ),
    GroupSpec(
        "media-recommend",
        "媒体推荐。",
        commands=(
            CommandSpec("media-sources", "GET", "/api/v1/mediaRecommend/mediaSources"),
            CommandSpec("channels", "GET", "/api/v1/mediaRecommend/channels/{media_source}", args=(arg("media_source", int, "mediaSource"),)),
            CommandSpec("page", "POST", "/api/v1/mediaRecommend/page", body_mode="json"),
            CommandSpec("options", "GET", "/api/v1/mediaRecommend/options", options=(qopt("media-source", wire_name="mediaSource", click_type=int), qopt("channel"))),
        ),
    ),
    GroupSpec(
        "media-person",
        "媒体人物查询。",
        commands=(
            CommandSpec("page", "GET", "/api/v1/mediaPerson/page", options=with_page()),
            CommandSpec("credits", "GET", "/api/v1/mediaPerson/credits/{id}", args=(arg("id", int),)),
        ),
    ),
    GroupSpec(
        "media-subject",
        "媒体片单。",
        commands=(
            CommandSpec("media-sources", "GET", "/api/v1/mediaSubject/mediaSources"),
            CommandSpec("categories", "GET", "/api/v1/mediaSubject/categories/{media_source}", args=(arg("media_source", int, "mediaSource"),)),
            CommandSpec("list", "GET", "/api/v1/mediaSubject/list", options=(qopt("category-code", wire_name="categoryCode"),)),
            CommandSpec("add", "POST", "/api/v1/mediaSubject/add", body_mode="json"),
            CommandSpec("delete", "DELETE", "/api/v1/mediaSubject/delete/{id}", args=(arg("id", int),)),
            CommandSpec("rename", "PUT", "/api/v1/mediaSubject/rename", body_mode="json"),
            CommandSpec("items", "GET", "/api/v1/mediaSubject/items", options=with_page(qopt("category-code", wire_name="categoryCode"), qopt("code"))),
        ),
    ),
    GroupSpec(
        "word-group",
        "词组管理。",
        commands=(
            CommandSpec("add", "POST", "/api/v1/wordGroup/add", body_mode="json"),
            CommandSpec("delete", "DELETE", "/api/v1/wordGroup/del/{id}", args=(arg("id", int),)),
            CommandSpec("batch-delete", "DELETE", "/api/v1/wordGroup/batchDel", body_mode="json"),
            CommandSpec("page", "GET", "/api/v1/wordGroup/page", options=with_page()),
            CommandSpec("clear", "DELETE", "/api/v1/wordGroup/clear"),
        ),
    ),
    GroupSpec(
        "word-unit",
        "词条管理。",
        commands=(
            CommandSpec("add", "POST", "/api/v1/wordUnit/add", body_mode="json"),
            CommandSpec("delete", "DELETE", "/api/v1/wordUnit/del/{id}", args=(arg("id", int),)),
            CommandSpec("batch-delete", "DELETE", "/api/v1/wordUnit/batchDel", body_mode="json"),
            CommandSpec("enabled", "POST", "/api/v1/wordUnit/enabled", body_mode="json"),
            CommandSpec("batch-import", "POST", "/api/v1/wordUnit/batchImport", body_mode="json"),
            CommandSpec("test", "POST", "/api/v1/wordUnit/test", body_mode="json"),
        ),
    ),
    GroupSpec(
        "filter-rule",
        "过滤规则。",
        commands=(
            CommandSpec("list", "GET", "/api/v1/filterRule/list"),
            CommandSpec("save", "POST", "/api/v1/filterRule/save", body_mode="json"),
            CommandSpec("detail", "GET", "/api/v1/filterRule/detail/{id}", args=(arg("id", int),)),
            CommandSpec("delete", "DELETE", "/api/v1/filterRule/delete/{id}", args=(arg("id", int),)),
            CommandSpec("copy", "POST", "/api/v1/filterRule/copy/{id}", args=(arg("id", int),)),
            CommandSpec("export", "GET", "/api/v1/filterRule/export/{id}", args=(arg("id", int),)),
            CommandSpec("import", "POST", "/api/v1/filterRule/import", body_mode="json"),
        ),
    ),
    GroupSpec(
        "filter-rule-detail",
        "过滤规则详情。",
        commands=(
            CommandSpec("list", "GET", "/api/v1/filterRuleDetail/list/{id}", args=(arg("id", int),)),
            CommandSpec("save", "POST", "/api/v1/filterRuleDetail/save", body_mode="json"),
            CommandSpec("detail", "GET", "/api/v1/filterRuleDetail/detail/{id}", args=(arg("id", int),)),
            CommandSpec("delete", "DELETE", "/api/v1/filterRuleDetail/delete/{id}", args=(arg("id", int),)),
            CommandSpec("copy", "POST", "/api/v1/filterRuleDetail/copy/{id}", args=(arg("id", int),)),
        ),
    ),
    GroupSpec(
        "path-sync",
        "路径同步。",
        commands=(
            CommandSpec("list", "GET", "/api/v1/pathsync/list"),
            CommandSpec("delete", "DELETE", "/api/v1/pathsync/delete/{id}", args=(arg("id", int),)),
            CommandSpec("save", "POST", "/api/v1/pathsync/save", body_mode="json"),
            CommandSpec("transfer", "POST", "/api/v1/pathsync/transfer", body_mode="json"),
            CommandSpec("test-rename", "POST", "/api/v1/pathsync/testRename", body_mode="json"),
            CommandSpec("run", "GET", "/api/v1/pathsync/run/{id}", args=(arg("id", int),)),
        ),
    ),
    GroupSpec(
        "path-sync-history",
        "路径同步历史。",
        commands=(
            CommandSpec("list", "GET", "/api/v1/pathsynchistory/list"),
            CommandSpec("delete", "DELETE", "/api/v1/pathsynchistory/delete/{id}", args=(arg("id", int),)),
            CommandSpec("save", "POST", "/api/v1/pathsynchistory/save", body_mode="json"),
            CommandSpec("page", "GET", "/api/v1/pathsynchistory/page", options=with_page()),
        ),
    ),
    GroupSpec(
        "media-server",
        "媒体服务器。",
        commands=(
            CommandSpec("list", "GET", "/api/v1/mediaServer/list"),
            CommandSpec("list-all-enabled", "GET", "/api/v1/mediaServer/listAllEnabled"),
            CommandSpec("save", "POST", "/api/v1/mediaServer/save", body_mode="json"),
            CommandSpec("detail", "GET", "/api/v1/mediaServer/detail/{id}", args=(arg("id", int),)),
            CommandSpec("delete", "DELETE", "/api/v1/mediaServer/delete/{id}", args=(arg("id", int),)),
            CommandSpec("types", "GET", "/api/v1/mediaServer/types"),
            CommandSpec("test", "POST", "/api/v1/mediaServer/test", body_mode="json"),
            CommandSpec("libraries", "GET", "/api/v1/mediaServer/libraries/{id}", args=(arg("id", int),)),
            CommandSpec("resume", "GET", "/api/v1/mediaServer/resume/{id}", args=(arg("id", int),), options=(qopt("num", click_type=int),)),
            CommandSpec("playing", "GET", "/api/v1/mediaServer/playing/{id}", args=(arg("id", int),)),
            CommandSpec("latest", "GET", "/api/v1/mediaServer/latest/{id}", args=(arg("id", int),), options=(qopt("num", click_type=int),)),
            CommandSpec("set-default", "PUT", "/api/v1/mediaServer/setDefault/{id}", args=(arg("id", int),), options=(qopt("default"),)),
        ),
    ),
    GroupSpec(
        "media-server-sync",
        "媒体服务器同步。",
        commands=(
            CommandSpec("save-config", "POST", "/api/v1/mediaServerSync/config/{id}", args=(arg("id", int),), body_mode="json"),
            CommandSpec("get-config", "GET", "/api/v1/mediaServerSync/config/{id}", args=(arg("id", int),)),
            CommandSpec("statistics", "GET", "/api/v1/mediaServerSync/statistics/{id}", args=(arg("id", int),)),
            CommandSpec("statistics-by-default", "GET", "/api/v1/mediaServerSync/statisticsByDefault"),
            CommandSpec("items", "GET", "/api/v1/mediaServerSync/items/{id}", args=(arg("id", int),), options=with_page(qopt("title"), qopt("media-type", wire_name="mediaType"), qopt("miss-eps", wire_name="missEps"))),
            CommandSpec("delete", "DELETE", "/api/v1/mediaServerSync/delete/{id}", args=(arg("id", int),)),
            CommandSpec("run", "GET", "/api/v1/mediaServerSync/run/{id}", args=(arg("id", int),)),
        ),
    ),
    GroupSpec(
        "search-tmdb",
        "TMDB 搜索缓存。",
        commands=(
            CommandSpec("page", "GET", "/api/v1/searchTmdb/page", options=with_page()),
            CommandSpec("save", "POST", "/api/v1/searchTmdb/save", body_mode="json"),
            CommandSpec("delete", "DELETE", "/api/v1/searchTmdb/delete", body_mode="json"),
            CommandSpec("clear", "DELETE", "/api/v1/searchTmdb/clear"),
            CommandSpec("clear-tmdb-cache", "DELETE", "/api/v1/searchTmdb/clearTmdbCache"),
        ),
    ),
    GroupSpec(
        "rename-preview",
        "重命名预览。",
        commands=(
            CommandSpec("replace", "POST", "/api/v1/renamePreview/replace", body_mode="json"),
            CommandSpec("seq", "POST", "/api/v1/renamePreview/seq", body_mode="json"),
            CommandSpec("append", "POST", "/api/v1/renamePreview/append", body_mode="json"),
        ),
    ),
    GroupSpec("scrape", "刮削任务。", commands=(CommandSpec("execute-path", "POST", "/api/v1/scrape/executePath", body_mode="json"),)),
    GroupSpec(
        "calendar",
        "媒体日历。",
        commands=(
            CommandSpec("media-types", "GET", "/api/v1/calendar/mediaTypes"),
            CommandSpec("platforms", "GET", "/api/v1/calendar/platforms", options=(qopt("media-type", wire_name="mediaType"),)),
            CommandSpec("calendar", "GET", "/api/v1/calendar/calendar", options=(qopt("media-type", wire_name="mediaType"), qopt("platform"), qopt("begin-date", wire_name="beginDate"), qopt("end-date", wire_name="endDate"))),
            CommandSpec("show-per-day", "GET", "/api/v1/calendar/showPerDayList", options=(qopt("media-type", wire_name="mediaType"), qopt("platform"), qopt("show-date", wire_name="showDate"))),
        ),
    ),
    GroupSpec(
        "transfer-fail",
        "转移失败记录。",
        commands=(
            CommandSpec("page", "GET", "/api/v1/transferFail/page", options=with_page()),
            CommandSpec("redo", "POST", "/api/v1/transferFail/redo", body_mode="json"),
            CommandSpec("redo-all", "GET", "/api/v1/transferFail/redoAll"),
            CommandSpec("delete", "DELETE", "/api/v1/transferFail/delete", body_mode="json"),
            CommandSpec("clear", "DELETE", "/api/v1/transferFail/clear"),
        ),
    ),
    GroupSpec(
        "transfer-history",
        "转移历史。",
        commands=(
            CommandSpec("page", "GET", "/api/v1/transferHistory/page", options=with_page()),
            CommandSpec("redo", "POST", "/api/v1/transferHistory/redo", body_mode="json"),
            CommandSpec("delete", "DELETE", "/api/v1/transferHistory/delete", body_mode="json"),
            CommandSpec("delete-source", "DELETE", "/api/v1/transferHistory/deleteSource", body_mode="json"),
            CommandSpec("delete-dest", "DELETE", "/api/v1/transferHistory/deleteDest", body_mode="json"),
            CommandSpec("delete-both", "DELETE", "/api/v1/transferHistory/deleteBoth", body_mode="json"),
            CommandSpec("clear", "DELETE", "/api/v1/transferHistory/clear"),
            CommandSpec("recover-strm-history", "POST", "/api/v1/transferHistory/recoverStrmHistory", body_mode="json"),
        ),
    ),
    GroupSpec(
        "douban-subject",
        "豆瓣片单搜索。",
        commands=(
            CommandSpec("search", "GET", "/api/v1/doubanSubject/search", options=with_page(qopt("title"))),
            CommandSpec("items", "GET", "/api/v1/doubanSubject/items", options=with_page(qopt("subject-id", wire_name="subjectId"), qopt("subject-type", wire_name="subjectType"))),
        ),
    ),
    GroupSpec(
        "douban",
        "豆瓣排行榜与片单。",
        commands=(
            CommandSpec("year-ranking", "GET", "/api/v1/douban/year/ranking", options=(qopt("type"), qopt("year", click_type=int))),
            CommandSpec("category-ranking", "GET", "/api/v1/douban/category/ranking", options=with_page(qopt("type"), qopt("category"))),
            CommandSpec("play-list", "GET", "/api/v1/douban/playList", options=with_page(qopt("category"), qopt("subject-type", wire_name="subjectType"))),
            CommandSpec("play-list-detail", "GET", "/api/v1/douban/playList/{id}/detail", args=(arg("id"),)),
            CommandSpec("dou-list-detail", "GET", "/api/v1/douban/douList/{id}/detail", args=(arg("id"),)),
        ),
    ),
)
