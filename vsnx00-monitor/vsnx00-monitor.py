"""VSNX00 datalogger monitor CLI.

Captures status, livedata, and feeds from ABB/Power-One/FIMER VSN300/VSN700
loggers and writes a prettified JSON file. Provides a simple command-line
interface with options to create a default config and to set logging levels.
"""

from __future__ import annotations

import argparse
import base64
import configparser
import json
import logging
import ssl
import sys
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import (
    HTTPBasicAuthHandler,
    HTTPDigestAuthHandler,
    HTTPPasswordMgrWithPriorAuth,
    build_opener,
    install_opener,
    parse_http_list,
    parse_keqv_list,
    urlopen,
)

LOGGER = logging.getLogger(__name__)


def make_request(requested_url: str):
    """Open a URL with a permissive SSL context and return the response.

    Returns None on error and logs details.
    """
    try:
        context = ssl.create_default_context()
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE
        return urlopen(requested_url, timeout=10, context=context)
    except HTTPError as error:
        LOGGER.error(
            "HTTPError: %s %s",
            getattr(error, "status", "?"),
            getattr(error, "reason", ""),
        )
    except URLError as error:
        LOGGER.error("URLError: %s", getattr(error, "reason", ""))
    except TimeoutError:
        LOGGER.error("Request timed out")
    return None


class VSN300HTTPDigestAuthHandler(HTTPDigestAuthHandler):
    """HTTP Digest auth handler for VSN300 using the non-standard X-Digest header."""

    def retry_http_digest_auth(self, req, auth):
        """Retry HTTP digest auth using the X-Digest header used by VSN300."""
        token, challenge = auth.split(" ", 1)
        chal = parse_keqv_list(parse_http_list(challenge))
        auth_hdr = self.get_authorization(req, chal)
        if auth_hdr:
            auth_val = f"X-Digest {auth_hdr}"
            if req.headers.get(self.auth_header, None) == auth_val:
                return None
            req.add_unredirected_header(self.auth_header, auth_val)
            return urlopen(req, timeout=req.timeout)
        return None

    def http_error_auth_reqed(self, auth_header, host, req, headers):
        """Handle authentication required responses by retrying with X-Digest."""
        authreq = headers.get(auth_header, None)
        if self.retried > 5:
            # Stop infinite retry loops
            raise HTTPError(
                req.get_full_url(), 401, "digest auth failed", headers, None
            )
        self.retried += 1
        if authreq:
            scheme = authreq.split()[0]
            if scheme.lower() == "x-digest":
                return self.retry_http_digest_auth(req, authreq)
        return None


class VSN700HTTPPreemptiveBasicAuthHandler(HTTPBasicAuthHandler):
    """Preemptive Basic Auth handler for VSN700.

    Instead of waiting for a 401/403 to then retry with credentials,
    send credentials immediately if the URL is handled by the password manager.
    """

    def http_request(self, req):
        """Attach Authorization header if credentials are available for the URL."""
        url = req.get_full_url()
        realm = ""
        # Very similar to retry_http_basic_auth(), but returns a request object.
        user, pw = self.passwd.find_user_password(realm, url)
        if pw:
            raw = f"{user}:{pw}"
            raw_b64 = base64.standard_b64encode(raw.encode("utf-8"))
            auth_val = f"Basic {raw_b64.decode('utf-8').strip()}"
            req.add_unredirected_header(self.auth_header, auth_val)
        return req

    https_request = http_request


class VSNX00Reader:
    """Reader for VSNX00 endpoints (status, livedata, feeds)."""

    def __init__(self, url: str, user: str, password: str) -> None:
        """Initialize the reader with base URL and credentials."""
        self.logger = logging.getLogger(__name__)

        self.url = url
        parsed_url = urlparse(url)
        self.host = parsed_url.hostname
        self.user = user
        self.password = password
        self.realm = ""

        self.status_data: dict = {}
        self.live_data: dict = {}
        self.feeds_data: dict = {}
        self.vsnx00_data: dict = {}

        self.passman = HTTPPasswordMgrWithPriorAuth()
        self.passman.add_password(self.realm, self.url, self.user, self.password)
        self.handler_vsn300 = VSN300HTTPDigestAuthHandler(self.passman)
        self.handler_vsn700 = VSN700HTTPPreemptiveBasicAuthHandler(self.passman)
        self.opener = build_opener(self.handler_vsn700, self.handler_vsn300)
        install_opener(self.opener)

    def get_vsnx00_status_data(self) -> dict | None:
        """Fetch and return the /v1/status JSON payload as a dict."""
        url_status_data = f"{self.url}/v1/status"

        self.logger.info("Getting VSNX00 status data from: %s", url_status_data)

        self.logger.info("Opening status URL")
        json_response = make_request(url_status_data)
        if json_response is None:
            return None
        self.logger.info("JSON to object")
        parsed_json = json.load(json_response)

        self.logger.debug("======= get_vsnx00_status_data(): parsed_json ===========")
        self.logger.debug("%s", parsed_json)
        self.logger.debug("======= get_vsnx00_status_data(): END ===========")

        return parsed_json

    def get_vsnx00_live_data(self) -> dict | None:
        """Fetch and return the /v1/livedata JSON payload as a dict."""
        url_live_data = f"{self.url}/v1/livedata"

        self.logger.info("Getting VSNX00 livedata from: %s", url_live_data)

        self.logger.info("Opening livedata URL")
        json_response = make_request(url_live_data)
        if json_response is None:
            return None
        self.logger.info("JSON to object")
        parsed_json = json.load(json_response)

        self.logger.debug("======= get_vsnx00_live_data(): parsed_json ===========")
        self.logger.debug("%s", parsed_json)
        self.logger.debug("======= get_vsnx00_live_data(): END ===========")

        return parsed_json

    def get_vsnx00_feeds_data(self) -> dict | None:
        """Fetch and return the /v1/feeds JSON payload as a dict."""
        url_feeds_data = f"{self.url}/v1/feeds"

        self.logger.info("Getting VSNX00 feeds data from: %s", url_feeds_data)

        self.logger.info("Opening feeds URL")
        json_response = make_request(url_feeds_data)
        if json_response is None:
            return None
        self.logger.info("JSON to object")
        parsed_json = json.load(json_response)

        self.logger.debug("======= get_vsnx00_feeds_data(): parsed_json ===========")
        self.logger.debug("%s", parsed_json)
        self.logger.debug("======= get_vsnx00_feeds_data(): END ===========")

        return parsed_json


def get_vsnx00_data(config: configparser.RawConfigParser) -> str | None:
    """Collect status, livedata, and feeds, merge and return JSON string.

    Writes a prettified JSON file named vsnx00_data.json as a side effect.
    Returns the JSON string, or None if any endpoint failed.
    """
    logger = logging.getLogger(__name__)

    pv_url = config.get("VSNX00", "url").lower()
    pv_user = config.get("VSNX00", "username")
    pv_password = config.get("VSNX00", "password")

    status_data: dict
    live_data: dict
    feeds_data: dict
    vsnx00_data: dict = {}

    logger.info("Capturing live data from ABB VSNX00 logger")
    pv_meter = VSNX00Reader(pv_url, pv_user, pv_password)

    # VSNx00 status
    logger.debug("Start - get_vsnx00_status_data")
    status_data = pv_meter.get_vsnx00_status_data() or {}
    if not status_data:
        logger.warning("No status_data received from VSNX00 logger. Exiting.")
        return None
    vsnx00_data.update(status_data)
    logger.debug("End - get_vsnx00_status_data")

    # VSNx00 livedata
    logger.debug("Start - get_vsnx00_live_data")
    live_data = pv_meter.get_vsnx00_live_data() or {}
    if not live_data:
        logger.warning("No live_data received from VSNX00 logger. Exiting.")
        return None
    vsnx00_data.update(live_data)
    logger.debug("End - get_vsnx00_live_data")

    # VSNx00 feeds
    logger.debug("Start - get_vsnx00_feeds_data")
    feeds_data = pv_meter.get_vsnx00_feeds_data() or {}
    if not feeds_data:
        logger.warning("No feeds_data received from VSNX00 logger. Exiting.")
        return None
    vsnx00_data.update(feeds_data)
    logger.debug("End - get_vsnx00_feeds_data")

    logger.debug("======= get_vsnx00_data(): vsnx00_data ===========")
    logger.debug("%s", vsnx00_data)
    logger.debug("======= get_vsnx00_data(): END ===========")

    # Write the prettified JSON to a file
    out_path = Path("vsnx00_data.json")
    out_path.write_text(json.dumps(vsnx00_data, indent=2), encoding="utf-8")

    # JSONify and prettify the three merged dicts
    return json.dumps(vsnx00_data, indent=2)


def write_config(path: str) -> None:
    """Write a default configuration file to the given path."""
    config = configparser.ConfigParser(allow_no_value=True)

    config.add_section("VSNX00")
    config.set(
        "VSNX00", "# url: URL of the VSN datalogger (including HTTP/HTTPS prefix)"
    )
    config.set("VSNX00", "# username: guest or admin")
    config.set("VSNX00", "# password: if user is admin, set the password")
    config.set("VSNX00", "# ")
    config.set("VSNX00", "url", "192.168.1.112")
    config.set("VSNX00", "username", "guest")
    config.set("VSNX00", "password", "pw")

    out_path = Path(path).expanduser()

    with out_path.open("w", encoding="utf-8") as configfile:
        config.write(configfile)

    LOGGER.info("Config has been written to: %s", out_path)


def read_config(path: str) -> configparser.RawConfigParser:
    """Read configuration from the given path, or exit with error if missing."""
    cfg_path = Path(path)
    if not cfg_path.is_file():
        LOGGER.error("Config file not found: %s", cfg_path)
        sys.exit(2)

    config = configparser.RawConfigParser()
    config.read(path)

    return config


def main() -> int | None:
    """Program entrypoint for the VSNX00 monitor CLI."""
    # Init
    default_cfg = "vsnx00-monitor.cfg"

    parser = argparse.ArgumentParser(description="VSNX00 Monitor help")
    parser.add_argument(
        "-c",
        "--config",
        nargs="?",
        const=default_cfg,
        help="config file location",
        metavar="path/file",
    )
    parser.add_argument(
        "-w",
        "--writeconfig",
        nargs="?",
        const=default_cfg,
        help="create a default config file",
        metavar="path/file",
    )
    parser.add_argument(
        "-v", "--verbose", help="verbose logging", action="store_true", default=False
    )
    parser.add_argument(
        "-d", "--debug", help="debug logging", action="store_true", default=False
    )

    args = parser.parse_args()

    # Set logging
    logger = logging.getLogger()

    if args.verbose:
        logger.setLevel(logging.INFO)
    elif args.debug:
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.WARNING)

    # create console handler and set level to debug
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)

    # create formatter
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    # add formatter to ch
    ch.setFormatter(formatter)

    # add ch to logger
    logger.addHandler(ch)

    if args.writeconfig:
        write_config(args.writeconfig)
        sys.exit(0)

    if args.config is None:
        path = default_cfg
    else:
        path = args.config

    path = str(Path(path).expanduser())

    config = read_config(path)

    logger.info("STARTING VSNX00 data capture")
    vsnx00_data = get_vsnx00_data(config)

    if vsnx00_data is None:
        logger.error("Error capturing data. Exiting...")
        return 1

    logger.info("Data capture complete. Here's the JSON data:")
    logger.info("========= VSNX00 Data =========")
    logger.info("%s", vsnx00_data)
    logger.info("========= VSNX00 Data =========")
    logger.info("Data capture complete, file vsnx00_data.json created.")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main() or 0)
    except KeyboardInterrupt:  # pragma: no cover - CLI convenience
        LOGGER.info("Ctrl-C received, exiting")
        sys.exit(130)
