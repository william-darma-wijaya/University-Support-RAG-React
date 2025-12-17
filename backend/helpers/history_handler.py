import os
import json
from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.chat_history import BaseChatMessageHistory
from langchain_community.chat_message_histories import ChatMessageHistory

class HistoryHandler:
    def __init__(self, sessions_path):
        self.store = {}
        self.session_path = sessions_path

    def get_session_history(self, session_id: str) -> BaseChatMessageHistory:
        if session_id not in self.store:
            history_file = os.path.join(self.session_path, f"{session_id}.json")
            if os.path.exists(history_file):
                with open(history_file, "r") as f:
                    messages = json.load(f)
                    history = ChatMessageHistory()
                    for msg in messages:
                        if msg['role'] == 'human':
                            history.add_user_message(msg['content'])
                        elif msg['role'] == 'ai':
                            history.add_ai_message(msg['content'])
                    self.store[session_id] = history
            else:
                self.store[session_id] = ChatMessageHistory()
        return self.store[session_id]
    
    def save_session_history(self, session_id: str):
        if session_id in self.store:
            history = self.store[session_id]
            messages = []
            for message in history.messages:
                if isinstance(message, HumanMessage):
                    messages.append({"role": "human", "content": message.content})
                elif isinstance(message, AIMessage):
                    messages.append({"role": "ai", "content": message.content})
            history_file = os.path.join(self.session_path, f"{session_id}.json")
            with open(history_file, "w") as f:
                json.dump(messages, f, indent=2)