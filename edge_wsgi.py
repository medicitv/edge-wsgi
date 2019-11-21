import sys
import json
import logging
from base64 import b64decode, b64encode
from io import BytesIO
from urllib.parse import urlencode

LOGGER = logging.getLogger("edge-wsgi")

__author__ = "Antoine Monnt"
__email__ = "amonnet@medici.tv"
__version__ = "1.0.0"

__all__ = ("make_lambda_handler",)

CONTENT_TYPE = "application/vnd.edge-wsgi+json"

def make_lambda_handler(viewer_request_app=None, viewer_response_app=None, origin_request_app=None, origin_response_app=None, binary_support=False):
    """
    Turn a WSGI app callable into a Lambda handler function suitable for
    running on API Gateway.
    """

    def handler(event, context):
        environ = get_environ(event, binary_support=binary_support)
        response = Response(binary_support=binary_support)

        LOGGER.debug('handler event', event)

        wsgi_app = None
        if environ["edge_wsgi.event_type"] == "viewer-request":
            wsgi_app = viewer_request_app
        elif environ["edge_wsgi.event_type"] == "viewer-response":
            wsgi_app = viewer_response_app
        elif environ["edge_wsgi.event_type"] == "origin-request":
            wsgi_app = origin_request_app
        elif environ["edge_wsgi.event_type"] == "origin-response":
            wsgi_app = origin_response_app

        if not wsgi_app:
            return

        result = wsgi_app(environ, response.start_response)
        response.consume(result)
        response = response.as_edge_response()

        LOGGER.debug('handler response', response)

        return response

    return handler


def get_environ(event, binary_support):

    cf = event["Records"][0]["cf"]
    event_type = cf["config"]["eventType"]
    request = cf['request']
    method = request["method"]
    body = request.get("body", {}).get("data", "")
    if request.get("body",{}).get("encoding", None) == "base64" :
        body = b64decode(body)
    else:
        body = body.encode("utf-8")
    params = request.get("querystring") or {}

    environ = {
        "CONTENT_LENGTH": str(len(body)),
        "HTTP": "on",
        "PATH_INFO": request["uri"],
        "QUERY_STRING": urlencode(params),
        "REMOTE_ADDR": request["clientIp"],
        "REQUEST_METHOD": method,
        "SCRIPT_NAME": "",
        "SERVER_PROTOCOL": "HTTP/1.1",
        "wsgi.errors": sys.stderr,
        "wsgi.input": BytesIO(body),
        "wsgi.multiprocess": False,
        "wsgi.multithread": False,
        "wsgi.run_once": False,
        "wsgi.version": (1, 0),
        "wsgi.url_scheme": "https",
    }

    headers = request.get("headers") or {}  # may be None when testing on console
    for key, value in headers.items():
        key = key.upper().replace("-", "_")

        if key == "CONTENT_TYPE":
            environ["CONTENT_TYPE"] = value[0]["value"]
        elif key == "HOST":
            environ["SERVER_NAME"] = value[0]["value"]

        environ["HTTP_" + key] = value[0]["value"]

    # Pass the AWS context to the application
    environ["edge_wsgi.event_type"] = event_type
    environ["edge_wsgi.config"] = cf["config"]
    environ["edge_wsgi.request"] = cf["request"]
    if "response" in cf:
        environ["edge_wsgi.response"] = cf["response"]

    return environ


class Response(object):
    def __init__(self, binary_support):
        self.status_code = 500
        self.headers = []
        self.body = BytesIO()
        self.binary_support = binary_support

    def start_response(self, status, response_headers, exc_info=None):
        if exc_info is not None:
            raise exc_info[0](exc_info[1]).with_traceback(exc_info[2])
        self.status_code, self.reason = status.split(" ", 1)
        self.headers.extend(response_headers)
        return self.body.write

    def consume(self, result):
        try:
            for data in result:
                if data:
                    self.body.write(data)
        finally:
            if hasattr(result, "close"):
                result.close()

    def as_edge_response(self):
        headers = {
            k.lower(): [dict(key=k, value= v)]
            for k, v in self.headers
            if k not in ('Content-Length', )
        }
        if "content-type" in headers and headers["content-type"][0]["value"] == CONTENT_TYPE:
            return json.loads(self.body().getvalue())

        response = {"status": self.status_code, "statusDescription": self.reason}
        response["headers"] = headers

        if len(self.body.getvalue()):
            if self._should_send_binary():
                response["bodyEncoding"] = "base64"
                response["body"] = b64encode(self.body.getvalue()).decode("utf-8")
            else:
                response["bodyEncoding"] = "text"
                response["body"] = self.body.getvalue().decode("utf-8")

        return response

    def _should_send_binary(self):
        """
        Determines if binary response should be sent to API Gateway
        """
        if not self.binary_support:
            return False

        content_type = self._get_content_type()
        non_binary_content_types = ("text/", "application/json")
        if not content_type.startswith(non_binary_content_types):
            return True

        content_encoding = self._get_content_encoding()
        # Content type is non-binary but the content encoding might be.
        return "gzip" in content_encoding.lower()

    def _get_content_type(self):
        return self._get_header("content-type") or ""

    def _get_content_encoding(self):
        return self._get_header("content-encoding") or ""

    def _get_header(self, header_name):
        header_name = header_name.lower()
        matching_headers = [v for k, v in self.headers if k.lower() == header_name]
        if len(matching_headers):
            return matching_headers[-1]
        return None
