===================================
Django Debug Toolbar Requests Panel
===================================

The Django Debug Toolbar Requests Panel (no less) is a plugin that provides
debug information about HTTP requests done with Kenneth Reitz' HTTP library,
`requests`.

Installation
============

Add the following lines to your ``settings.py``::

   INSTALLED_APPS = (
       ...
       'debug_toolbar_requests',
       ...
   )

   DEBUG_TOOLBAR_PANELS = (
       ...
       'debug_toolbar_requests.panel.RequestsDebugPanel',
       ...
   )

An extra panel titled "HTTP Requests" should appear in your debug toolbar.

Screenshot
==========

.. image:: https://raw.github.com/enginous/django-debug-toolbar-requests/master/docs/images/screenshots/main.png
