#!/bin/bash

# Script to update all config property accesses to method calls
# This changes config.embedding_model_instance to config.embedding_model_instance()

cd /Users/longle/CoverGo-AI-Hackathon/SurfSense/surfsense_backend

# Find and replace in all Python files
find app -name "*.py" -type f -exec sed -i '' \
  -e 's/config\.embedding_model_instance\b/config.embedding_model_instance()/g' \
  -e 's/config\.chunker_instance\b/config.chunker_instance()/g' \
  -e 's/config\.code_chunker_instance\b/config.code_chunker_instance()/g' \
  -e 's/config\.reranker_instance\b/config.reranker_instance()/g' \
  {} \;

echo "Fixed all config property calls to use lazy-loading methods"
