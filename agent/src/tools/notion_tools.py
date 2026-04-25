import os
import json
import requests
from pathlib import Path
from dotenv import load_dotenv
import xml.etree.ElementTree as ET
from langgraph.types import Command
from agent.src.graph.state import Todo, MainAgentState
from langchain.messages import ToolMessage
from langgraph.prebuilt import InjectedState
from description import WRITE_TODOS_DESCRIPTION
from typing_extensions import Annotated, Optional
from langchain_core.tools import tool, InjectedToolCallId


load_dotenv(Path(__file__).resolve().parents[2] / ".env")
PUB_MED_KEY = os.getenv("PUB_MED_KEY")


WORKSPACE_DIR = Path(__file__).parent.parent / "memory"