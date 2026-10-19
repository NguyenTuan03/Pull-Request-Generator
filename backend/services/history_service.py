import json
import os
import uuid
from datetime import datetime
from typing import List
from backend.models.pr_model import HistoryItem


class HistoryService:
    def __init__(self, storage_path: str = "data/history.json"):
        self.storage_path = storage_path
        self._ensure_storage()

    def _ensure_storage(self):
        folder = os.path.dirname(self.storage_path)
        if folder and not os.path.exists(folder):
            os.makedirs(folder, exist_ok=True)
        if not os.path.exists(self.storage_path):
            with open(self.storage_path, "w", encoding="utf-8") as f:
                json.dump([], f)

    def save_item(self, pr_url: str, pr_title: str, model_used: str, summary_markdown: str) -> HistoryItem:
        items = self.get_all()
        item = HistoryItem(
            id=str(uuid.uuid4())[:8],
            created_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            pr_url=pr_url,
            pr_title=pr_title or "Pull Request Summary",
            model_used=model_used,
            summary_markdown=summary_markdown,
        )
        # Đưa item mới nhất lên đầu, giới hạn tối đa 50 bản ghi
        items.insert(0, item)
        items = items[:50]

        with open(self.storage_path, "w", encoding="utf-8") as f:
            json.dump([i.model_dump() for i in items], f, ensure_ascii=False, indent=2)

        return item

    def get_all(self) -> List[HistoryItem]:
        self._ensure_storage()
        try:
            with open(self.storage_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                return [HistoryItem(**item) for item in data]
        except Exception:
            return []

    def get_recent(self, limit: int = 15) -> List[HistoryItem]:
        all_items = self.get_all()
        return all_items[:limit]

    def clear(self) -> bool:
        try:
            with open(self.storage_path, "w", encoding="utf-8") as f:
                json.dump([], f)
            return True
        except Exception:
            return False
