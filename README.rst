=========
edge-wsgi
=========

Wrap a WSGI application in an AWS Lambda handler function for running on
lambda@edge

A quick example:

.. code-block:: python

    from edge_wsgi import make_lambda_handler
    from myapp.wsgi import app

    # Configure this as your entry point in AWS Lambda
    lambda_handler = make_lambda_handler(app)


Installation
============

Use **pip**:

.. code-block:: sh

    pip install edge-wsgi

Python 3.8 or later supported.

Usage
=====

``make_lambda_handler(viewer_request_app=None, viewer_response_app=None, origin_request_app=None, origin_response_app=None, binary_support=False)``
--------------------------------------------------

``app`` should be a WSGI app, for example from Django's ``wsgi.py`` or Flask's
``Flask()`` object.

If you want to support sending binary responses, set ``binary_support`` to
``True``.

Note that binary responses aren't sent if your response has a 'Content-Type'
starting 'text/html' or 'application/json' - this is to support sending larger
text responses.
