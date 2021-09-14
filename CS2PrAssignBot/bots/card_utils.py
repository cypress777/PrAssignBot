from copy import deepcopy
from typing import Dict, List, Union

from botbuilder.schema import ChannelAccount
from botbuilder.schema.teams import TeamsChannelAccount


def construct_select_group_card(
    WI: str, 
    pr_link: str,
    description: str,
    task_groups: List[str],
    selected: bool,
):
    select_group_card = {
        "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
        "type": "AdaptiveCard",
        "version": "1.3",
        "body": [
            _pr_basic_info(WI, pr_link, description),
            _text_block_placeholder(),
        ]
    }

    if not selected:
        select_group_card["body"].append(
            {
                "type": "TextBlock",
                "text": "Select task group for your PR",
                "weight": "bolder",
            }
        )
        select_group_card["actions"] = [
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

        return _construct_unselect_card_choice_set(select_group_card, task_groups)
    else:
        select_group_card["body"].append(
            {
                "type": "TextBlock",
                "text": "Selected task group for your PR",
                "weight": "bolder",
            }
        )
        return _construct_selected_card(select_group_card, task_groups)

def _construct_unselect_card_choice_set(select_group_card: Dict, task_groups) -> Dict:
    choices_set = {
        "type": "Input.ChoiceSet",
        "id": "TaskGroup",
        "style": "expanded",
        "isMultiSelect": False,
        "value": "General",
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

def _construct_selected_card(select_group_card: Dict, task_groups) -> Dict:
    for task_group in task_groups:
        select_group_card["body"].append(
            {
                "type": "TextBlock",
                "text": task_group,
                "color": "accent",
                "weight": "bolder",
            },
        )
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
            _pr_basic_info(WI, pr_link, description),
            _text_block_placeholder(),
        ],
        "actions": [
            {
                "type": "Action.Submit",
                "title": "Delete",
                "data": {
                    "action": "deletethiscard"
                }
            }
        ]
    }

    _add_review_info(review_card, reviewee, reviewers, added_members)

    review_card["body"].extend(
        [
            _text_block_placeholder(),
            _text_block_placeholder(),
        ]
    )

    return review_card


def _add_review_info(
    review_card: Dict,
    reviewee: Union[ChannelAccount, TeamsChannelAccount],
    reviewers: List[str],
    added_members: List[Union[ChannelAccount, TeamsChannelAccount]],
):
    review_info = {
        "type": "FactSet",
        "facts": [
            {
                "title": "Reviewee",
                "value": "<at>{}</at>".format(reviewee.name)
            },
        ]
    }

    mentions = {
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

    reviewer_string = ""

    for reviewer in reviewers:
        if len(reviewer_string) > 0:
            reviewer_string += ","

        added = False
        for added_member in added_members:
            if added_member.name == reviewer:
                mentions["entities"].append(
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
    review_card["msteams"] = mentions
        

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
                "text": "{} Task Groups".format(task_groups.get("team_name", "")),
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
                    "text": "{} ({})".format(group_name, len(group_members))
                }
            ],
        }

        for member_name in group_members:
            group_info["items"].append(
                {
                    "type": "TextBlock",
                    "text": "" + member_name,
                    "spacing": "Small",        
                }
            )

        group_info_card["body"].append(group_info)

    return group_info_card


def _pr_basic_info(WI: str, link: str, description: str) -> Dict:
    return {
        "type": "Container",
        "items": [
            {
                "type": "TextBlock",
                "size": "large",
                "weight": "bolder",
                "text": "{}".format(WI)
            },
            {
                "type": "TextBlock",
                "size": "medium",
                "text": "[click to review]({})".format(link)
            },
            {
                "type": "TextBlock",
                "size": "small",
                "text": description,
                "wrap": True,
            },
        ]
    }

def _text_block_placeholder() -> Dict:
    return {
        "type": "TextBlock",
        "text": " ",
    }
