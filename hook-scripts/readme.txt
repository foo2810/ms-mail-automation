The following JSON is passed to your hook scripts via stdin:

{
  "subject": "Sample Mail",
  "content_type": "text",
  "content": "TEST\n\n\n________________________________________\n差出人: Joho Doe <john-doe@example.com>\n送信日時: 2026年2月28日 8:28\n宛先: jane-doe@example.com\n件名: Sample Mail\n\nThis is test mail.\n",
  "sender": {
    "name": "John Doe",
    "address": "john-doe@example.com"
  },
  "to_recipients": [
    {
      "name": "Jane Doe",
      "address": "jane-doe@example.com"
    }
  ],
  "cc_recipients": [],
  "bcc_recipients": [],
  "created_date_time": "2026-03-01 02:28:18+09:00",
  "received_date_time": "2026-03-01 02:29:56+09:00",
  "sent_date_time": "2026-03-01 02:29:49+09:00"
}