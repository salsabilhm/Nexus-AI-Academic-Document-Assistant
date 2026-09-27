# Nexus — AI Academic Document Assistant

**Live Demo:** https://nexus-ai-academic-document-assistan.vercel.app/

Nexus helps university students work with their academic documents. Upload
university requirements, guidelines and templates alongside your own research,
then ask Nexus what is missing, unclear or out of place — with the sources
behind every answer.

## Problem

Students routinely check a thesis or report against a pile of PDFs: faculty
requirements, formatting guidelines, and assessment criteria. It is slow, easy
to miss a section, and hard to know which rule came from which document.

## Solution

Nexus reads those documents and allows students to:

- retrieve the parts relevant to their questions;
- understand the required structure of their academic work;
- compare university requirements with their research document;
- identify missing or unclear sections;
- receive answers grounded in the provided documents;
- see the sources behind the answers.

## Architecture

```text
React Frontend
      ↓
Django REST API
      ↓
Document Processing
      ↓
RAG Retrieval
      ↓
Agent
      ↓
LLM
