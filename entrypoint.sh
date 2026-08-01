#!/bin/sh
set -e

JS_FILE="${FRONTEND_DIST}/env.js"

TMPFILE=$(mktemp)
env | grep '^FRONTEND_' | sort > "$TMPFILE"

{
    printf "window.__RUNTIME_CONFIG__ = {\n"
    first=true
    while IFS='=' read -r raw_key value; do
        key="${raw_key#FRONTEND_}"
        escaped=$(printf '%s' "$value" | sed 's/\\/\\\\/g; s/"/\\"/g')
        if [ "$first" = true ]; then
            first=false
        else
            printf ",\n"
        fi
        printf '    %s: "%s"' "$key" "$escaped"
    done < "$TMPFILE"
    printf "\n};\n"
} > "$JS_FILE"

rm -f "$TMPFILE"

exec "$@"
