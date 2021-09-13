from typing import Dict, List, Union

from botbuilder.schema import ChannelAccount
from botbuilder.schema.teams import TeamsChannelAccount


def construct_select_group_card(
    WI: str, 
    pr_link: str,
    description: str,
    reviewee: Union[ChannelAccount, TeamsChannelAccount],
    task_groups: Dict[str, List]
):
    select_group_card = {
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
                        "text": "link: {}".format(pr_link)
                    },
                    {
                        "type": "TextBlock",
                        "size": "small",
                        "text": description
                    },
                ]
            },
            {
                "type": "TextBlock",
                "text": "Select task group for your PR",
                "weight": "bolder",
            },
            
        ],
        "actions": [
            {
                "type": "Action.Submit",
                "title": "OK",
                "data": {
                    "action": "submitpr",
                    "WI": WI,
                    "PrLink": pr_link,
                    "Description": description,
                }
            }
        ]
    }

    choices_set = {
        "type": "Input.ChoiceSet",
        "id": "TaskGroup",
        "style": "expanded",
        "isMultiSelect": False,
        "choices": [
            {
                "title": "General",
                "value": "General"
            },
        ]
    }

    for group in task_groups:
        choices_set["choices"].append(
            {
                "title": group,
                "value": group,
            }
        )

    select_group_card["body"].append(choices_set)

    return select_group_card

def construct_pr_submit_form(
    WI: str, 
    pr_link: str,
    description: str,
    reviewee: Union[ChannelAccount, TeamsChannelAccount],
    reviewers: List[str],
    added_members: List[Union[ChannelAccount, TeamsChannelAccount]],
): 
    review_card = {
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
                        "text": "link: {}".format(pr_link)
                    },
                    {
                        "type": "TextBlock",
                        "size": "small",
                        "text": description
                    },
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

    review_info = {
        "type": "FactSet",
        "facts": [
            {
                "title": "Reviewee",
                "value": "<at>{}</at>".format(reviewee.name)
            },
        ]
    }

    reviewer_string = ""

    for reviewer in reviewers:
        if len(reviewer_string) > 0:
            reviewer_string += ","
            
        added = False
        for added_member in added_members:
            if added_member.name == reviewer:
                review_card["msteams"]["entities"].append(
                    {
                        "type": "mention",
                        "text": "<at>{}</at>".format(reviewer),
                        "mentioned": {
                            "id": added_member.id,
                            "name": reviewer
                        }
                    }
                )
                reviewer_string += " <at>{}</at>".format(reviewer)
                added = True
                break
        if not added:
            reviewer_string += " " + reviewer

    review_info["facts"].append(
        {
            "title": "Reviewers",
            "value": reviewer_string,
        }
    )
    review_card["body"].append(review_info)

    return review_card
        

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
