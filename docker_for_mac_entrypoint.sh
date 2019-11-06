#!/bin/bash

socat tcp-listen:5000,reuseaddr,fork tcp:host.docker.internal:5000 &
socat tcp-listen:5009,reuseaddr,fork tcp:host.docker.internal:5009 &
echo "Forwarding localhost:5000,5009 to host.docker.internal"

exec "$@"
