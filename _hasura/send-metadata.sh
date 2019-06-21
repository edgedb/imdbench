#! /bin/bash
curl -d'{"type":"replace_metadata", "args":'$(cat metadata.json)'}' \
	'http://localhost:8080/v1/query'