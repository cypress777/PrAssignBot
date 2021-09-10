from botbuilder.schema import ChannelAccount


def construct_pr_submit_form(WI: str, pr_link: str, description: str, current_time: str, reviewee: ChannelAccount): 
    return {
                "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
                "type": "AdaptiveCard",
                "version": "1.3",
                "body": [
                    {
                        "type": "Container",
                        "items": [
                            {
                                "type": "TextBlock",
                                "size": "large",
                                "weight": "bolder",
                                "text": "WI: {}".format(WI)
                            },
                            {
                                "type": "TextBlock",
                                "size": "medium",
                                "text": pr_link
                            },
                            {
                                "type": "TextBlock",
                                "size": "small",
                                "text": description
                            },
                            {
                                "type": "FactSet",
                                "facts": [
                                    {
                                        "title": "Reviewee",
                                        "value": "<at>{}</at>".format(reviewee.name)
                                    },
                                    {
                                        "title": "Assigned to:",
                                        "value": "Not Assigned"
                                    },
                                    {
                                        "title": "Start date:",
                                        "value": current_time
                                    }
                                ]
                            }
                        ]
                    },
                ],
                "actions": [
                    {
                        "type": "Action.Submit",
                        "title": "Delete This Review Request",
                        "data": {
                            "action": "deletethiscard"
                        }
                    }
                ],
                "msteams": {
                    "entities": [
                        {
                            "type": "mention",
                            "text": "<at>{}</at>".format(reviewee.name),
                            "mentioned": {
                                "id": reviewee.id,
                                "name": reviewee.name
                            }
                        }
                    ]
                }
            }
