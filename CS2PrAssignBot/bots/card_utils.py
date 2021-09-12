from typing import List

from botbuilder.schema import ChannelAccount
from botbuilder.schema.teams import TeamDetails, TeamsChannelAccount


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

def construct_group_info_card(team_info: TeamDetails, team_members: List[TeamsChannelAccount]):
    group_info_card = {
        "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
        "type": "AdaptiveCard",
        "version": "1.3",
        "body": [
            {
                "type": "TextBlock",
                "size": "large",
                "weight": "bolder",
                "text": team_info.name,
            },
            {
                "type": "Container",
                "items": [
                    {
                        "type": "TextBlock",
                        "size": "medium",
                        "weight": "bolder",
                        "text": "Group Members ({})".format(len(team_members))
                    },
                ]
            },
        ],
    }

    for member in team_members:
        group_info_card["body"][1]["items"].append(
            {
                "type": "TextBlock",
                "text": member.name,
                "spacing": "Small",        
            }
        )

    return group_info_card
