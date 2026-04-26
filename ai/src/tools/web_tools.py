import os
from dotenv import load_dotenv
from exa_py import Exa
from langchain.tools import tool
from datetime import datetime

load_dotenv()

exa_client = Exa(api_key=os.environ.get("EXA_API_KEY"))

@tool
def search_web(query : str, num_results : int = 5) -> str:
    """
    EXA API를 사용하여 웹 검색을 수행합니다.

    최신 연구 동향, 기술 정보, 논문, 문서 등을 검색할 때 사용

    Args:
        query : 검색할 쿼리
        num_reuslts : 반환할 결과 수 (기본값 : 5)
    """