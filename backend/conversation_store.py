from typing import Dict, List

class ConversationStore:
    def __init__(self):
        self._sessions: Dict[str, List[dict]] = {}

    def get_history(self, session_id: str) -> List[dict]:
        return self._sessions.setdefault(session_id, [])

    def add_message(self, session_id: str, role: str, content: str):
        history = self.get_history(session_id)
        history.append({"role": role, "content": content})

    def reset(self, session_id: str):
        self._sessions[session_id] = []

store = ConversationStore()