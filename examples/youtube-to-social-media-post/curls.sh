#!/bin/bash

# Default to the 'social_media_post' endpoint if no argument is passed
ENDPOINT="social_media_post"
if [[ "$1" == "streaming_async" ]]; then
  ENDPOINT="social_media_post_streaming_async"
elif [[ "$1" == "streaming" ]]; then
  ENDPOINT="social_media_post_streaming"
fi

# Perform the curl request to the chosen endpoint
curl -X 'GET' "http://localhost:7443/$ENDPOINT" \
  -s -H 'Accept: application/json' \
  --no-buffer | jq --unbuffered -c '.' | while IFS= read -r line; do
    if [[ "$line" != "" ]]; then  # Check for non-empty lines
      clear
      echo "$line" | jq --color-output .
      sleep .01  # Add a small delay for visual clarity
    fi
done
