## 프레임워크 아키텍처는 다음과 같다
1. Messages 입력
2. Commit_agent가 messages를 보고 논문검색(research), 논문 분석(paper_analysis), 과제관련논문 찾기(task_paper_research) task 중 하나를 선택해서 수행해 (일단 논문 검색만 구현)
3. 논문 검색에서 사용자 메시지를 보고 메시지를 다시 new_messages로 변환하고, 관련 topic : list[str], task : str 형식으로 저장해 
4. 이 new_messages와 topic, task를 Main Agent에게 보내면 해당 task에 해당하는 sub-agent로 이동해 (지금은 research agent로 이동)
5. 이제 research-agent로 이동하면, pubMed tool, arXiv tool을 사용해서, 논문 정보를 memory에 중복을 제외하고 저장해
6. 이 논문 정보를 relevance agent에게 주고 new_messages, topic을 기반으로 관련도 점수를 정하고 이 중 top-5개만 memory에 저장해
7.  이 저장된 논문의 실제로 다운받고 해당 논문을 summary agent가 읽고 요약해서 memory에 저장해
8.  이제 이 요약된 정보를 validation agent가 다시 new_messages, topic을 기반으로 잘 찾았는지 평가하고 그렇지 않으면 다시 Research Agent가 동작해서 1 ~ 8번을 수행해, 만약 잘 찾았다고 평가하면 final_report를 작성해서 memory에 저장해