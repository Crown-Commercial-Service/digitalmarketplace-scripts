#!/bin/sh

[ -n "$TESTDIR" ] && cd $TESTDIR/../..

[ -d /usr/local/opt/coreutils/libexec/gnubin ] && PATH="/usr/local/opt/coreutils/libexec/gnubin:$PATH"

[ -n "$AWS_ACCOUNT" ] || AWS_ACCOUNT=test

# Create folder for command stubs
mkdir -p $TMPDIR/stubs
export PATH="$TMPDIR/stubs:$PATH"

# Stub out aws-auth
cat > $TMPDIR/stubs/aws-auth << 'EOF'
exec $@
EOF
chmod +x $TMPDIR/stubs/aws-auth

# Stub out sops
cat > $TMPDIR/stubs/sops << EOF
#!/bin/sh
cat $TESTDIR/config-file.fixture
EOF
chmod +x $TMPDIR/stubs/sops
