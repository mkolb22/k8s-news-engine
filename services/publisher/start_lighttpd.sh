#!/bin/sh

# Start lighttpd in foreground without PID file
exec lighttpd -D -f /etc/lighttpd/lighttpd.conf