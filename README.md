# agentic-rag-chatbot
--------------------------
대학생과 직장인의 효율적인 문서 업무를 지원하는 문서 작업 도우미입니다.

- .pdf, .hwp, .docs 등 여러 파일 형식과 웹사이트 url에 기능을 지원합니다.
- 문서를 업로드 후 질문을 입력하면 문서의 내용 + 실시간 검색 결과를 활용해 질문에 대한 답변을 생성합니다.
- 문서 검색 품질을 높이기 위해 Compression Retriever와 Reraker를 적용하였습니다.
- 답변의 신뢰성을 높이기 위해 응답 생성과 동시에 활용한 references를 함께 표시합니다.
- 다음에 이어질 질문 세트를 만들어 사용자에게 추천합니다.
