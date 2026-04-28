PAPER_SEARCH_MODELS = {
    "search-agent": {"model": "openai:gpt-4o-mini", "temperature": 0.0},
    "relevance-agent": {"model": "openai:gpt-4.1", "temperature": 0.0},
    "summarizer-agent": {"model": "openai:gpt-4.1", "temperature": 0.2},
    "validator-agent" : {"model" : "openai:gpt-5-mini", "temperature" : 0.2}
}

PAPER_SEARCH_CONFIG = {
    "max_iter" : 2,
}

COMMIT_MODELS = {
    "commit-agent" : {"model" : "openai:gpt-4o-mini", "temperature" : 0.7}
}

PAPER_ANALYSIS_MODELS = {
    "inspector-agent" : {"model" : "openai:gpt-4o-mini", "temperature":0.0},
}