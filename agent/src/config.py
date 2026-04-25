MAX_ITER = 1
GRAPH_RECURSION_LIMIT = 50
AGENT_RECURSION_LIMIT = 100
SEARCH_MAX_RESULTS_PER_SOURCE = 5
SUMMARY_RELEVANCE_THRESHOLD = 0.2
SUMMARY_MAX_PAPERS = 20
RELEVANCE_LLM_TOP_K = 30

SUBAGENT_MODELS = {
    "research-agent": {"model": "openai:gpt-4o-mini", "temperature": 0.0},
    "dedup-agent": {"model": "openai:gpt-4o-mini", "temperature": 0.0},
    "relevance-agent": {"model": "openai:gpt-4.1", "temperature": 0.0},
    "summarizer-agent": {"model": "openai:gpt-4.1", "temperature": 0.2},
}

TOPIC_MODELS = {
    "topic-agent" : {"model" : "openai:gpt-4o-mini", "temperature" : 0.2}
}

VALID_MODELS = {
    "valid-agent" : {"model" : "openai:gpt-4o-mini", "temperature" : 0.0}
}
