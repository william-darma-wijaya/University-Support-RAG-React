from langchain_ollama import OllamaLLM
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.chains import create_history_aware_retriever, create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.runnables.history import RunnableWithMessageHistory

class SimpleRAGChain:
    def __init__(self, retriever, model_name="qwen2.5:3b"):
        self.retriever = retriever
        self.model_name = model_name
        self.llm = self._get_ollama_model(model_name)
        self.chain = self._setup_chain()
        print("RAG Chain setup success!")

    def _get_ollama_model(self, model_name):
        try:
            print(f"Connecting to Ollama model: {model_name} ...")
            llm = OllamaLLM(model=model_name)
            print("Ollama connected!")
            return llm
        except Exception as e:
            print(f"Gagal menghubungkan ke Ollama. Pastikan model '{model_name}' sudah di-pull dan Ollama jalan.")
            print(f"Error detail: {e}")
            return None

    def _setup_chain(self):
        # untuk membuat contextualize question
        retriever_prompt = (
            "Diberikan riwayat percakapan dan pertanyaan terbaru dari pengguna"
            "yang kemungkinan merujuk pada konteks dalam riwayat percakapan tersebut,"
            "buatlah sebuah pertanyaan mandiri yang dapat dipahami tanpa melihat riwayat percakapan sebelumnya."
            "JANGAN menjawab pertanyaannya, cukup reformulasikan jika diperlukan,"
            "dan jika tidak perlu, kembalikan seperti adanya."
        )
        contextualize_question_prompt = ChatPromptTemplate.from_messages(
            [
                ("system", retriever_prompt),
                MessagesPlaceholder(variable_name="chat_history"),
                ("human", "{input}"),
            ]
        )
        history_aware_retriever = create_history_aware_retriever(self.llm, self.retriever, contextualize_question_prompt)

        system_prompt = (
            "Kamu adalah asisten pintar yang hanya menjawab berdasarkan konteks yang diberikan."
            "Gunakan informasi berikut untuk menjawab pertanyaan."
            "Jika tidak ada informasi yang relevan, cukup jawab dengan 'Saya tidak tahu, anda bisa menghubungi bagian terkait untuk masalah tersebut.'"
            "{context}"
        )
        question_answer_prompt = ChatPromptTemplate.from_messages(
            [
                ("system", system_prompt),
                MessagesPlaceholder(variable_name="chat_history"),
                ("human", "{input}"),
            ]
        )
        question_answer_chain = create_stuff_documents_chain(self.llm, question_answer_prompt)

        rag_chain = create_retrieval_chain(history_aware_retriever, question_answer_chain)

        return rag_chain

    def ask(self, question: str, chat_history, session_id) -> str:
        conversational_rag_chain = RunnableWithMessageHistory(
            self.chain,
            lambda _: chat_history,
            input_messages_key="input",
            history_messages_key="chat_history",
            output_messages_key="answer",
        )

        answer = ""
        for chunk in conversational_rag_chain.stream(
            {"input": question},
            config={
                "configurable": {"session_id": session_id}
            },
        ):
            if 'answer' in chunk:
                answer += chunk['answer']

        return answer