from typing import Dict, List

class ConversationStore:
    def __init__(self):
        self._sessions: Dict[str, List[dict]] = {}
        self._ended: Dict[str, bool] = {}

    def get_history(self, session_id: str) -> List[dict]:
        return self._sessions.setdefault(session_id, [])

    def add_message(self, session_id: str, role: str, content: str):
        history = self.get_history(session_id)
        history.append({"role": role, "content": content})

    def set_ended(self, session_id: str, value: bool = True):
        self._ended[session_id] = value

    def is_ended(self, session_id: str) -> bool:
        return self._ended.get(session_id, False)

    def reset(self, session_id: str):
        self._sessions[session_id] = []
        self._ended[session_id] = False

store = ConversationStore()