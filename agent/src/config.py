SUBAGENT_MODELS = {
    "research-agent": {"model": "openai:gpt-4o-mini", "temperature": 0.0},
    "dedup-agent": {"model": "openai:gpt-4o-mini", "temperature": 0.0},
    "relevance-agent": {"model": "openai:gpt-4.1", "temperature": 0.0},
    "summarizer-agent": {"model": "openai:gpt-4.1", "temperature": 0.2},
    "notion-agent": {"model": "openai:gpt-4o-mini", "temperature": 0.0},
}

TOPIC_MODELS = {
    "topic-agent" : {"model" : "openai:gpt-4o-mini", "temperature" : 0.2}
}

VALID_MODELS = {
    "valid-agent" : {"model" : "openai:gpt-4o-mini", "temperature" : 0.0}
}