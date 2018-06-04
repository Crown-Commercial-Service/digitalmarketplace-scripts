#!/bin/bash

socat tcp-listen:5000,reuseaddr,fork tcp:host.docker.internal:5000 &
socat tcp-listen:5001,reuseaddr,fork tcp:host.docker.internal:5001 &
echo "Forwarding localhost:5000-5001 to host.docker.internal"

exec "$@"
