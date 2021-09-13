from typing import Dict, Union

from botbuilder.schema import ChannelAccount
from botbuilder.schema.teams import TeamsChannelAccount


def construct_pr_submit_form(WI: str, pr_link: str, description: str, current_time: str, reviewee: Union[ChannelAccount, TeamsChannelAccount]): 
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
                                        "title": "Start date:",
                                        "value": current_time
                                    },
                                    {
                                        "title": "Reviewee",
                                        "value": "<at>{}</at>".format(reviewee.name)
                                    },
                                    {
                                        "title": "Assigned to:",
                                        "value": "Not Assigned"
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

def construct_group_info_card(task_groups: Dict):
    group_info_card = {
        "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
        "type": "AdaptiveCard",
        "version": "1.3",
        "body": [
            {
                "type": "TextBlock",
                "size": "large",
                "weight": "bolder",
                "text": task_groups.get("team_name", ""),
            },
        ],
    }

    for group_name, group_members in task_groups.get("groups", {}).items():
        group_info = {
            "type": "Container",
            "items": [
                {
                    "type": "TextBlock",
                    "size": "medium",
                    "weight": "bolder",
                    "text": "Task Group Name: {}".format(group_name)
                },
                {
                    "type": "TextBlock",
                    "size": "medium",
                    "weight": "bolder",
                    "text": "Task Group Members ({})".format(len(group_members))
                },
            ],
        }

        for member_name in group_members:
            group_info["items"].append(
                {
                    "type": "TextBlock",
                    "text": member_name,
                    "spacing": "Small",        
                }
            )

        group_info_card["body"].append(group_info)

    return group_info_card
