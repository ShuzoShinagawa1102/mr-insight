"""
rag – Django application package.

This app implements the RAG (Retrieval-Augmented Generation) pipeline:
  adaptor/   – external service adapters (OpenSearch, S3, …)
  agent/     – AI agents (Extract / EntityResolution / SchemaMapper / Verifier / Commit)
  context/   – context-building helpers
  document/  – document loaders and parsers
  model/     – Pydantic domain models (DTOs / value objects)
"""
