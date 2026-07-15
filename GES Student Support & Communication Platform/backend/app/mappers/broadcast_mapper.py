from app.models.models import Broadcast
from app.schemas.broadcasts import BroadcastOut

class BroadcastMapper:
    @staticmethod
    def to_out(broadcast: Broadcast) -> BroadcastOut:
        return BroadcastOut(
            id=broadcast.id,
            title=broadcast.title,
            content=broadcast.content,
            target_region_id=broadcast.target_region_id,
            target_school_id=broadcast.target_school_id,
            author_id=broadcast.author_id,
            created_at=broadcast.created_at
        )
