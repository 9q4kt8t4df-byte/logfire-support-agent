import uuid
from datetime import datetime
from typing import Optional
from sqlmodel import Field, Session, SQLModel, create_engine, select


class Conversation(SQLModel, table=True):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)


class Message(SQLModel, table=True):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    conversation_id: str = Field(foreign_key="conversation.id", index=True)
    role: str
    content: str
    created_at: datetime = Field(default_factory=datetime.utcnow)


class ConversationStore:
    def __init__(self, db_url: str = "sqlite:///conversations.db"):
        self.engine = create_engine(db_url)
        SQLModel.metadata.create_all(self.engine)

    def create_conversation(self) -> Conversation:
        conv = Conversation()
        with Session(self.engine) as session:
            session.add(conv)
            session.commit()
            session.refresh(conv)
        return conv

    def get_conversation(self, conversation_id: str) -> Optional[Conversation]:
        with Session(self.engine) as session:
            return session.get(Conversation, conversation_id)

    def add_message(self, conversation_id: str, role: str, content: str) -> Message:
        msg = Message(conversation_id=conversation_id, role=role, content=content)
        with Session(self.engine) as session:
            session.add(msg)
            session.commit()
            session.refresh(msg)
        return msg

    def get_messages(self, conversation_id: str) -> list[Message]:
        with Session(self.engine) as session:
            statement = (
                select(Message)
                .where(Message.conversation_id == conversation_id)
                .order_by(Message.created_at)
            )
            return list(session.exec(statement).all())
