from loguru import logger
import streamlit as st
from utills import print_message, get_session_history, get_conversation_chain, get_conversation_chain_with_callbacks, StreamHandler

from langchain_core.messages import ChatMessage
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import StrOutputParser
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_core.chat_history import BaseChatMessageHistory
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain.document_loaders import PyPDFLoader, Docx2txtLoader, CSVLoader, UnstructuredPowerPointLoader, TextLoader
from langchain.embeddings import OpenAIEmbeddings
from langchain.vectorstores import FAISS

st.set_page_config(page_title="MyAssistant", page_icon="🤗")
st.title("🤗 MyAssistant")

# side bar
with st.sidebar:
    session_id = st.text_input("Session ID", value="Chating Room")
    uploaded_file = st.file_uploader("Upload a file", type=['pdf', 'docx', 'csv', 'txt'], accept_multiple_files=True)

    if uploaded_file is not None:
        doc_list = []
        for doc in uploaded_file:
            file_name = doc.name
            with open(file_name, "wb") as file:
                file.write(doc.getvalue())
                logger.info(f"Uploaded {file_name}")
            try:
                if '.pdf' in doc.name:
                    loader = PyPDFLoader(file_name)
                    documents = loader.load_and_split()
                elif '.docx' in doc.name:
                    loader = Docx2txtLoader(file_name)
                    documents = loader.load_and_split()
                elif '.csv' in doc.name:
                    loader = CSVLoader(file_name)
                    documents = loader.load_and_split()
                elif '.txt' in doc.name:
                    loader = TextLoader(file_name, encoding="utf-8")
                    documents = loader.load_and_split()
                else:
                    st.error("Unsupported file type.")
                    continue

                doc_list.extend(documents)
            except Exception as e:
                st.error(f"Error loading {file_name}: {e}")
                logger.error(f"Error loading {file_name}: {e}")

        if st.button("Process") and doc_list:
            st.write("Document has been uploaded!")
        elif not doc_list:
            st.warning("No documents were loaded. Please check the file format.")

    if st.button("Reset"):
        st.session_state["message"] = []
        st.experimental_rerun()

# 메세지 내용을 기록하는 상태 변수
if "message" not in st.session_state:
    st.session_state["message"] = [] 

# 채팅 기록을 저장하는 상태 변수
if "store" not in st.session_state:
    st.session_state["store"] = dict()

# RAG 관련 변수 초기화
if "vector_store" not in st.session_state:
    if doc_list:
        try:
            embeddings = OpenAIEmbeddings()
            st.session_state["vector_store"] = FAISS.from_documents(doc_list, embeddings)
        except Exception as e:
            st.error(f"Error initializing vector store: {e}")
            logger.error(f"Error initializing vector store: {e}")

# 채팅 기록을 출력하는 함수
print_message()

# initialize chat box
if user_input := st.chat_input("메세지를 입력해 주세요"):

    # 사용자가 입력한 내용
    st.chat_message("user").write(f"{user_input}")
    st.session_state["message"].append(ChatMessage(role="user", content=user_input))

    # RAG 기능: 사용자의 질문에 대한 관련 문서 검색
    if "vector_store" in st.session_state:
        try:
            relevant_docs = st.session_state["vector_store"].similarity_search(user_input)

            # LLM 응답 생성
            llm = ChatOpenAI(model="gpt-4o-mini")
            prompt = ChatPromptTemplate.from_messages(
                [
                    ("system", "사용자의 질문에 짧고 간결한 답변을 생성해주세요."),
                    MessagesPlaceholder(variable_name="history"),
                    ("human", "{question}"),  # 검색된 문서 내용 추가
                ]
            )

            chain = prompt | llm
            chain_with_memory = RunnableWithMessageHistory(
                chain,
                get_session_history,
                input_messages_key="question",
                history_messages_key="history",
            )

            response = chain_with_memory.invoke(
                {"question": user_input},
                config={"configurable": {"session_id": session_id}}
            )
            answer = response.content

            # AI의 답변
            with st.chat_message("assistant"):
                stream_handler = StreamHandler(st.empty())
                llm = ChatOpenAI(model="gpt-4o-mini", streaming=True, callbacks=[stream_handler])
                prompt = ChatPromptTemplate.from_messages(
                    [
                        ("system", "사용자의 질문에 짧고 간결한 답변을 생성해주세요."),
                        MessagesPlaceholder(variable_name="history"),
                        ("human", "{question}") # 검색된 문서 내용 추가
                    ]
                )
                chain = prompt | llm
                chain_with_callbacks = RunnableWithMessageHistory(
                    chain,
                    get_session_history,
                    input_messages_key="question",
                    history_messages_key="history",
                )
                response = chain_with_callbacks.invoke(
                    {"question": user_input},
                    config={"configurable": {"session_id": session_id}}
                )
                st.session_state["message"].append(ChatMessage(role="assistant", content=answer))
        except Exception as e:
            st.error(f"Error during processing: {e}")
            logger.error(f"Error during processing: {e}")
    else:
        st.error("Vector store is not initialized.")