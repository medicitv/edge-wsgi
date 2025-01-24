import pytest
from edge_wsgi import make_lambda_handler


def test_make_lambda_handler():
    # Define a simple WSGI app for testing
    def simple_app(environ, start_response):
        status = '200 OK'
        response_headers = [('Content-type', 'text/plain')]
        start_response(status, response_headers)
        return [b"Hello World"]

    # Create a Lambda handler using the simple WSGI app
    handler = make_lambda_handler(viewer_request_app=simple_app)

    # Define a mock event and context
    event = {
        "Records": [
            {
                "cf": {
                    "config": {
                        "eventType": "viewer-request"
                    },
                    "request": {
                        "method": "GET",
                        "uri": "/",
                        "clientIp": "127.0.0.1",
                        "headers": {
                            "host": [{"key": "Host", "value": "localhost"}]
                        }
                    }
                }
            }
        ]
    }
    context = {}

    # Call the handler and check the response
    response = handler(event, context)
    assert response['status'] == '200'
    assert response['body'] == "Hello World"
    assert response['headers']['content-type']


if __name__ == "__main__":
    pytest.main()
