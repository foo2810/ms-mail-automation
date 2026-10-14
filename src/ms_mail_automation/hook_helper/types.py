import json
import datetime
import dataclasses
from typing import Self, List


@dataclasses.dataclass(frozen=True)
class MSMessage:
    subject: str = ""
    content_type: str = "text"
    content: str = ""
    sender: dict = dataclasses.field(default_factory=dict)
    to_recipients: List[str] = dataclasses.field(default_factory=list)
    cc_recipients: List[str] = dataclasses.field(default_factory=list)
    bcc_recipients: List[str] = dataclasses.field(default_factory=list)
    created_date_time: datetime.datetime = datetime.datetime(1980, 1, 1)
    received_date_time: datetime.datetime = datetime.datetime(1980, 1, 1)
    sent_date_time: datetime.datetime = datetime.datetime(1980, 1, 1)

    def __str__(self):
        return f"{self.sender.get('name')} <{self.sender.get('address')}> {self.content_type} {len(self.content)} chars"

    def to_json(self) -> dict:
        return {
            "subject": self.subject,
            "content_type": self.content_type,
            "content": self.content,
            "sender": self.sender,
            "to_recipients": self.to_recipients,
            "cc_recipients": self.cc_recipients,
            "bcc_recipients": self.bcc_recipients,
            "created_date_time": self.created_date_time.isoformat(),
            "received_date_time": self.received_date_time.isoformat(),
            "sent_date_time": self.sent_date_time.isoformat(),
        }

    def to_json_str(self) -> str:
        return json.dumps(self.to_json())

    @staticmethod
    def from_json(ms_message: dict) -> Self:
        args = {}

        if "subject" not in ms_message:
            raise ValueError("value of .subject not found")
        args["subject"] = ms_message["subject"]

        if "content_type" not in ms_message:
            raise ValueError("value of .content_type not found")
        args["content_type"] = ms_message["content_type"]

        if "content" not in ms_message:
            raise ValueError("value of .content not found")
        args["content"] = ms_message["content"]

        if "sender" not in ms_message:
            raise ValueError("value of .sender not found")
        if "name" not in ms_message["sender"]:
            raise ValueError("value of .sender.name not found")
        if "address" not in ms_message["sender"]:
            raise ValueError("value of .sender.address not found")
        args["sender"] = ms_message["sender"]

        for ty_recipient in ["to_recipients", "cc_recipients", "bcc_recipients"]:
            if ty_recipient not in ms_message:
                raise ValueError(f"value of .{ty_recipient} not found")

            for r in ms_message[ty_recipient]:
                if "name" not in r:
                    raise ValueError(f"value of .{ty_recipient}.name not found")
                if "address" not in r:
                    raise ValueError(f"value of .{ty_recipient}.address not found")

            args[ty_recipient] = ms_message[ty_recipient]

        if "created_date_time" not in ms_message:
            raise ValueError("value of .created_date_time not found")
        if "received_date_time" not in ms_message:
            raise ValueError("value of .received_date_time not found")
        if "sent_date_time" not in ms_message:
            raise ValueError("value of .sent_date_time not found")

        args["created_date_time"] = datetime.datetime.fromisoformat(
            ms_message["created_date_time"]
        )
        args["received_date_time"] = datetime.datetime.fromisoformat(
            ms_message["received_date_time"]
        )
        args["sent_date_time"] = datetime.datetime.fromisoformat(
            ms_message["sent_date_time"]
        )

        return MSMessage(**args)
