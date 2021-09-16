from typing import Dict, List, Union

from botbuilder.schema import ChannelAccount
from botbuilder.schema.teams import TeamsChannelAccount


def construct_select_group_card(
    WI: str, 
    review_link: str,
    description: str,
    reviewers: str,
    task_groups: List[str],
    selected: bool,
):
    select_group_card = {
        "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
        "type": "AdaptiveCard",
        "version": "1.3",
        "body": [
            _review_basic_info(WI, review_link, description),
            _text_block_placeholder(),
            _text_block_placeholder(),
            _text_block_placeholder(),
        ]
    }

    if not selected:
        select_group_card["body"].extend(
            [
                {
                    "type": "TextBlock",
                    "text": "Select reviewers",
                    "weight": "bolder",
                },
                {
                    "type": "Input.Text",
                    "id": "Reviewers",
                    "placeholder": "Assign to specified reviewers, separated by comma.",
                },
                _text_block_placeholder(),
                _text_block_placeholder(),
                _text_block_placeholder(),
                {
                    "type": "TextBlock",
                    "text": "Or, select task group to randomly choose reviewers from",
                    "weight": "bolder",
                },
                {
                    "type": "Input.Number",
                    "label": "Number of Reviewers",
                    "id": "NumberOfReviewers",
                    "placeholder": "Number of Reviewers",
                    "min": 1,
                    "max": 5,
                    "value": 1,
                }
            ]
        )

        _construct_unselect_group_choice_set(select_group_card, task_groups)

        select_group_card["actions"] = [
            {
                "type": "Action.Submit",
                "title": "OK",
                "data": {
                    "action": "submitpr",
                    "WI": WI,
                    "ReiviewLink": review_link,
                    "Description": description,
                }
            }
        ]
    else:
        assert (len(reviewers.strip()) > 0 or len(task_groups) > 0 and len(task_groups[0]) > 0), "At least specify one of Reviewers or TaskGroup."

        if len(reviewers) > 0:
            _construct_selected_reviewers(select_group_card, reviewers)
        else:
            _construct_selected_group(select_group_card, task_groups)

    return select_group_card

def _construct_unselect_group_choice_set(select_group_card: Dict, task_groups):
    choices_set = {
        "type": "Input.ChoiceSet",
        "label": "Task Group",
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

def _construct_selected_reviewers(select_group_card: Dict, reviewers):
    select_group_card["body"].append(
        {
            "type": "TextBlock",
            "text": "Selected reviewers",
            "weight": "bolder",
        }
    )

    select_group_card["body"].append(
        {
            "type": "TextBlock",
            "text": reviewers,
            "color": "accent",
            "weight": "bolder",
        },
    )

def _construct_selected_group(select_group_card: Dict, task_groups):
    select_group_card["body"].append(
        {
            "type": "TextBlock",
            "text": "Selected task group for your review",
            "weight": "bolder",
        }
    )

    for task_group in task_groups:
        select_group_card["body"].append(
            {
                "type": "TextBlock",
                "text": task_group,
                "color": "accent",
                "weight": "bolder",
            },
        )

def construct_review_submit_form(
    WI: str, 
    review_link: str,
    description: str,
    reviewee: Union[ChannelAccount, TeamsChannelAccount],
    reviewers: List[str],
    saved_members: List[Dict],
): 
    review_card = {
        "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
        "type": "AdaptiveCard",
        "version": "1.3",
        "body": [
            _review_basic_info(WI, review_link, description),
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

    _add_review_info(review_card, reviewee, reviewers, saved_members)

    review_card["body"].extend(
        [_text_block_placeholder(), _text_block_placeholder()]
    )

    return review_card


def _add_review_info(
    review_card: Dict,
    reviewee: Union[ChannelAccount, TeamsChannelAccount],
    reviewers: List[str],
    saved_members: List[Dict],
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

        saved = False
        for saved_member in saved_members:
            if saved_member["name"] == reviewer:
                mentions["entities"].append(
                    {
                        "type": "mention",
                        "text": "<at>{}</at>".format(reviewer),
                        "mentioned": {
                            "id": saved_member["id"],
                            "name": reviewer
                        }
                    }
                )
                reviewer_string += " <at>{}</at>".format(reviewer)
                saved = True
                break
        if not saved:
            reviewer_string += " " + reviewer

    review_info["facts"].append(
        {
            "title": "Reviewers",
            "value": reviewer_string,
        }
    )

    review_card["body"].append(review_info)    
    review_card["msteams"] = mentions
        

def construct_group_info_card(task_groups: Dict, saved_members: List[Dict]):
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
            _text_block_placeholder(),
            _text_block_placeholder(),
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
            member = {
                "type": "TextBlock",
                "text": "" + member_name,
                "spacing": "small",
                "color": "accent",
            }
            if _is_saved_member(member_name, saved_members):
                member["weight"] = "bolder"

            group_info["items"].append(member)

        group_info_card["body"].append(group_info)
        group_info_card["body"].append(_text_block_placeholder())

    return group_info_card

def _is_saved_member(member_name: str, saved_members: List[Dict]):
    for saved_member in saved_members:
        if saved_member["name"] == member_name:
            return True
    return False

def _review_basic_info(WI: str, link: str, description: str) -> Dict:
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
                "text": "[review link]({})".format(link)
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

