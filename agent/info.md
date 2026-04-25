
# AI 논문 검색 에이전트 - 개선된 파이프라인 (Topic-first 구조)

## 📌 전체 파이프라인 개요

```
사용자 입력
   ↓
[1️⃣ Topic Expansion Agent] 세부 토픽 후보 생성
   ↓
[2️⃣ Topic Decision Router] 자동 진행 / 사용자 확인 / 추가 질문 결정
   ↓
[3️⃣ Main Agent] Todo 생성 및 실행 계획 수립
   ↓
[4️⃣ Paper Search] 4개 API 병렬 검색
   ↓
[5️⃣ Dedup] DOI / arXiv / PMID / Title 기반 중복 제거
   ↓
[6️⃣ Relevance Judge] 제목 + 초록 기반 관련도 점수화
   ↓
[7️⃣ Summarizer] threshold 이상 논문만 요약
   ↓
[8️⃣ Notion Writer] 최종 결과 저장
```

---

# 🔧 단계별 상세 설명

## 1️⃣ Topic Expansion Agent — 세부 토픽 생성

### 목적

사용자 입력을 검색 가능한 topic 후보로 확장

### 입력

```json
{
  "user_query": "Genomics와 AI 논문 찾아줘"
}
```

### 처리

다음 수행:

- main topic 추출
- domain 분리
- 세부 research topic 생성 (10~30개)
- ambiguity_score 계산
- clarification 필요 여부 판단

### 출력

```json
{
  "candidate_topics": [
    {
      "topic": "Deep learning for variant calling",
      "keywords": ["variant calling", "deep learning", "genomics"]
    },
    {
      "topic": "Transformer models for gene expression prediction",
      "keywords": ["transformer", "gene expression", "genomics"]
    }
  ],
  "ambiguity_score": 0.72,
  "needs_user_clarification": true,
  "clarification_question": "variant calling, gene expression, single-cell analysis, DNA sequencing 중 어떤 방향을 찾으시나요?"
}
```

---

## 2️⃣ Topic Decision Router — 진행 여부 판단

### 목적

pipeline 실행 방향 결정

### 처리 로직

```
if ambiguity_score < threshold:
    자동 진행

elif needs_user_clarification == True:
    사용자에게 질문

elif candidate_topics > max_topics:
    사용자 선택 요청
```

### 결과

```
approved_topics 생성
```

예:

```json
{
  "approved_topics": [
    "Deep learning for variant calling"
  ]
}
```

---

## 3️⃣ Main Agent — Todo 생성 및 실행 계획 수립

### 목적

pipeline orchestration

### 입력

```json
{
  "approved_topics": [
    "Deep learning for variant calling"
  ]
}
```

### 처리

생성:

- domains
- search scope
- 최소 논문 수
- 실행 전략
- todo list

### 출력

```json
{
  "domains": ["Genomics", "AI"],
  "search_scope": "last_3_years",
  "min_papers": 50,
  "todos": [
    "variant calling 관련 논문 검색",
    "중복 제거",
    "관련도 평가",
    "요약 생성",
    "Notion 저장"
  ]
}
```

---

## 4️⃣ Paper Search — 논문 병렬 검색

### 목적

학술 DB에서 metadata 수집

### 검색 API

| API | 역할 |
|-----|------|
| Semantic Scholar | citation 포함 |
| PubMed | 생물학 중심 |
| arXiv | 최신 ML 논문 |
| Crossref | coverage 보완 |

### 처리

각 topic마다:

```
4개 API 병렬 호출
```

### 출력

```json
{
  "raw_papers": [...],
  "total_raw_papers": 1247
}
```

---

## 5️⃣ Dedup — 중복 제거

### 목적

동일 논문 제거

### 기준

우선순위:

1. DOI
2. arXiv ID
3. PMID
4. Title similarity

### 출력

```json
{
  "deduplicated_papers": [...],
  "total_deduplicated": 847,
  "duplicates_removed": 400
}
```

---

## 6️⃣ Relevance Judge — 관련도 평가

### 목적

Main topic 대비 논문 관련성 점수화

### 입력

Title + Abstract

### 출력

```json
{
  "paper_id": "...",
  "relevance_score": 0.92
}
```

---

## 7️⃣ Summarizer — 논문 요약 생성

### 목적

관련도 높은 논문만 요약

### 기준

```
relevance_score >= 0.70
```

### 출력

```json
{
  "paper_id": "...",
  "summary": "..."
}
```

---

## 8️⃣ Notion Writer — 결과 저장

### 목적

최종 논문 metadata 저장

### 저장 필드

- Title
- Authors
- Year
- DOI
- URL
- Abstract
- Summary
- Relevance Score
- Source
- Tags
- Status

### 출력

```json
{
  "total_papers_written": 295,
  "success": 295
}
```
