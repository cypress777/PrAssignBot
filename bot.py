import traceback
from datetime import date
import connexion


def echo():
    data_packet = connexion.request.json

    try:
        current_time = date.today().strftime("%d/%m/%Y")

        sender = data_packet['from']['name']
        task_info = data_packet['text'].lstrip('<at>cyp-tester</at>').rstrip('\n')

        message = { "type": "message"}
        message['attachments'] = [
            {
                "contentType": "application/vnd.microsoft.card.adaptive",
                "content": {
                    "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
                    "type": "AdaptiveCard",
                    "version": "1.0",
                    "body": [
                        {
                            "type": "Container",
                            "items": [
                                {
                                    "type": "TextBlock",
                                    "text": "Hi teams {} has updated a task: {}".format(sender, task_info)
                                },
                                {
                                    "type": "FactSet",
                                    "facts": [
                                        {
                                            "title": "Created by",
                                            "value": sender,
                                        },
                                        {
                                            "title": "Assigned to:",
                                            "value": "Not Assigned",
                                        },
                                        {
                                            "title": "Start date:",
                                            "value": current_time,
                                        }
                                    ]
                                }
                            ]
                        }
                    ],
                    "actions": [
                        {
                            "type": "Action.ShowCard",
                            "title": "Set due date",
                            "card": {
                            "type": "AdaptiveCard",
                            "body": [
                                {
                                "type": "Input.Date",
                                "id": "dueDate"
                                }
                            ],
                            "actions": [
                                {
                                "type": "Action.Submit",
                                "title": "OK"
                                }
                            ]
                            }
                        },
                        {
                            "type": "Action.ShowCard",
                            "title": "Comment",
                            "card": {
                            "type": "AdaptiveCard",
                            "body": [
                                {
                                "type": "Input.Text",
                                "id": "comment",
                                "isMultiline": True,
                                "placeholder": "Enter your comment"
                                }
                            ],
                            "actions": [
                                {
                                "type": "Action.Submit",
                                "title": "OK"
                                }
                            ]
                            }
                        }
                    ],
                },
            }
        ]

        return message
    except Exception:
        stacktrace = traceback.format_exc()
        return stacktrace, 500
