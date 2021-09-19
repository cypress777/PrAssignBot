from typing import Any, List, Optional, Union, Dict
import json
import os
import pathlib
import random
from botbuilder.core import CardFactory, TurnContext, MessageFactory
from botbuilder.core.teams import TeamsActivityHandler, teams_get_channel_id, TeamsInfo
from botbuilder.schema import ConversationParameters, ChannelAccount
from botbuilder.schema.teams import (
    TeamInfo,
    TeamsChannelAccount,
    MessagingExtensionActionResponse,
    MessagingExtensionAction,
)
import copy

import bots.card_utils as bot_utils


TEAM_MEMBERS_FILE_NAME = "team_members.json"
TEAM_CONFIG_FILE_NAME = "team_config.json"

class PrAssignBot(TeamsActivityHandler):
    def __init__(self, app_id: str, app_password: str):
        self._team_config_file = os.path.join(os.path.dirname(__file__), TEAM_CONFIG_FILE_NAME)
        self._team_member_file = os.path.join(os.path.dirname(__file__), TEAM_MEMBERS_FILE_NAME)

        self._app_id = app_id
        self._app_password = app_password

        self._team_config: Dict[str, Any] = self._load_team_config()
        self._general_task_group: List[str] = self._init_general_task_group(self._team_config["groups"])
        self._saved_team_members: List[Dict] = self._load_saved_team_members()

    async def on_teams_members_added(  # pylint: disable=unused-argument
        self,
        teams_members_added: List[TeamsChannelAccount],
        team_info: TeamInfo,
        turn_context: TurnContext,
    ):
        for member in teams_members_added:
            if member.id != turn_context.activity.recipient.id:
                await self._send_help_card(turn_context, member)

    async def on_teams_messaging_extension_submit_action_dispatch(
        self, turn_context: TurnContext, action: MessagingExtensionAction
    ) -> MessagingExtensionActionResponse:
        if "submitpr" in action.command_id.strip().lower():
            error_message = self.check_review_submission(turn_context.activity.from_property.name, action.data)

            if error_message:
                await turn_context.send_activity(MessageFactory.text(error_message))
                await self._select_group_for_review(turn_context, action.data)
            else:
                await self._submit_review(turn_context, action.data)

            return MessagingExtensionActionResponse()

        raise NotImplementedError(f"Unexpected action.command_id {action.command_id}.")

    async def on_message_activity(self, turn_context: TurnContext):
        TurnContext.remove_recipient_mention(turn_context.activity)

        if turn_context.activity.text:
            text = turn_context.activity.text.strip().lower()

            if "show" in text:
                await self._send_task_group_card(turn_context)
                return

            if "addme" in text:
                await self._send_add_user_card(turn_context)
                return

        if turn_context.activity.value:
            value: Dict = turn_context.activity.value

            if value.get("action", None):
                if "deletethiscard" in value["action"].strip().lower():
                    await self._delete_card_activity(turn_context)
                    return

                if "submitpr" in value["action"].strip().lower():
                    error_message = self.check_review_submission(turn_context.activity.from_property.name, value)
                    if error_message:
                        await turn_context.send_activity(MessageFactory.text(error_message))
                    else:
                        await self._update_select_group_card(turn_context, value)
                        await self._submit_review(turn_context, value)
                    return

        # TODO: create help card
        await self._send_help_card(turn_context)

    def check_reviewer_numbers(self, reviewers_number: int) -> bool:
        return 0 <= reviewers_number < len(self._general_task_group)

    def check_name_match_unique_member(self, name: str, group: List[str]) -> bool:
        count = 0
        for member in group:
            if self.check_name_match(member, name):
                count += 1

        return count == 1

    @staticmethod
    def check_name_match(actual: str, name: str) -> bool:
        if actual.strip().lower() == name.strip().lower():
            return True

        if actual.strip().lower().replace(" ", "") == name.strip().lower():
            return True

        for part in actual.split(" "):
            if part.strip().lower() == name.strip().lower():
                return True

        return False

    def check_review_submission(self, reviewee: str, data: Dict) -> Optional[str]:
        reviewers_string = data.get("Reviewers", "")
        task_group = data.get("TaskGroup", "")
        reviewer_number = int(data.get("NumberOfReviewers", "0"))

        assigned = len(reviewers_string.replace(" ", "").replace(",", "")) > 0
        if not assigned and len(task_group) == 0:
            return "*Please specify Reiviewers Or TaskGroup*"

        invalid_reviewers_error_message = self._get_invalid_reviewers_error_message(reviewee, reviewers_string.split(","))
        if assigned and invalid_reviewers_error_message:
            return "*Invalid reviewers: {}*".format(invalid_reviewers_error_message)

        if not self.check_reviewer_numbers(reviewer_number):
            return "*Incorrect reviewer number: {}, total team members: {}*".format(
                reviewer_number,
                len(self._general_task_group),
            )

        specified_reviewers = self._get_reviewer_list_from_string(reviewers_string)
        if not self.check_reviewer_numbers(reviewer_number + len(specified_reviewers)):
            return "*Too many reviewers: {}, total team members: {}*".format(
                reviewer_number + len(specified_reviewers),
                len(self._general_task_group),
            )

    @staticmethod
    def _init_general_task_group(groups: Dict[str, List]) -> List[str]:
        members = []
        for group in groups.values():
            members.extend(group)

        return list(set(members))

    def _get_invalid_reviewers_error_message(self, reviewee: str, reviewers: List[str]) -> Optional[str]:
        invalid_string = None
        for reviewer in reviewers:
            if not self.check_name_match_unique_member(reviewer, self._general_task_group) or self.check_name_match(reviewee, reviewer):
                if invalid_string:
                    invalid_string += f", {reviewer}"
                else:
                    invalid_string = reviewer

                if self.check_name_match(reviewee, reviewer):
                    invalid_string += "[reviewee]"
            
        return invalid_string

    async def _select_group_for_review(
        self,
        turn_context: TurnContext,  # pylint: disable=unused-argument
        data: Dict,
    ):
        select_card = CardFactory.adaptive_card(
            bot_utils.construct_select_group_card(
                data["WI"],
                data["ReiviewLink"],
                data["Description"],
                data.get("Reviewers", ""),
                self._team_config["groups"].keys(),
                selected=False,
            )
        )

        await turn_context.send_activity(MessageFactory.attachment(attachment=select_card))

    async def _update_select_group_card(
        self,
        turn_context: TurnContext,
        data: Dict,
    ):
        selected_card = CardFactory.adaptive_card(
            bot_utils.construct_select_group_card(
                data["WI"],
                data["ReiviewLink"],
                data["Description"],
                data.get("Reviewers", ""),
                [data.get("TaskGroup")] if data.get("TaskGroup") else [],
                selected=True,
            )
        )

        selected_group_message = MessageFactory.attachment(attachment=selected_card)
        selected_group_message.id = turn_context.activity.reply_to_id
        await turn_context.update_activity(selected_group_message)

    def _get_valid_group_name(self, group_name: str) -> Optional[str]:
        for name in self._team_config["groups"]:
            if group_name.strip().lower() == name.lower():
                return name
        return None

    # TODO: count task assigned to each reviewers, add weight to them
    def _assign_reviewers(self, reviewee: str, task_group_name: str, number_of_reviewers, excluded_members: List[str]) -> List[str]:
        task_group_name = self._get_valid_group_name(task_group_name)
        if not task_group_name or len(self._team_config["groups"][task_group_name]) == 0:
            group = self._general_task_group
        else:
            group = self._team_config["groups"][task_group_name]

        excluded_members.append(reviewee)

        assign_from_group = [member for member in group if member not in excluded_members]

        reviewers = []
        if number_of_reviewers >= len(assign_from_group):
            reviewers.extend(assign_from_group)
            excluded_members.extend(reviewers)

            assign_from_general_group = [member for member in self._general_task_group if member not in excluded_members]
            reviewers.extend(
                self._extract_members(
                    number_of_reviewers - len(assign_from_group),
                    assign_from_general_group
                )
            )
        else:
            reviewers = self._extract_members(number_of_reviewers, assign_from_group)

        return reviewers

    @staticmethod
    def _extract_members(number: int, group: List[str]) -> List[str]:
        members = []
        while number > 0 and len(group) > 0:
            member = random.choice(group)
            members.append(member)
            group.remove(member)
            number -= 1
        return members

    def _get_reviewer_list_from_string(self, reviewers_string: str) -> List[str]:
        reviewers = reviewers_string.split(",")
        formated_reviewers = []

        for reviewer in reviewers:
            if not self.check_name_match_unique_member(reviewer, self._general_task_group):
                continue

            for actual_reviewer in self._general_task_group:
                if self.check_name_match(actual_reviewer, reviewer):
                    formated_reviewers.append(actual_reviewer)
                    break
        
        return formated_reviewers

    async def _submit_review(
        self,
        turn_context: TurnContext,  # pylint: disable=unused-argument
        data: Dict,
    ):
        reviewee: Union[ChannelAccount, TeamsChannelAccount] = turn_context.activity.from_property

        reviewers = []
        if data.get("Reviewers", None):
            reviewers = self._get_reviewer_list_from_string(data.get("Reviewers"))

        number_of_reviewers = int(data.get("NumberOfReviewers", "0"))
        if number_of_reviewers > 0:
            excluded_members = copy.deepcopy(reviewers)
            excluded_members.append(reviewee.name)
            reviewers.extend(self._assign_reviewers(reviewee.name, data.get("TaskGroup", ""), number_of_reviewers, excluded_members))

        review_card = CardFactory.adaptive_card(
            bot_utils.construct_review_submit_form(
                data["WI"],
                data["ReiviewLink"],
                data["Description"],
                reviewee,
                reviewers,
                self._saved_team_members,
            )
        )
        submit_review_message = MessageFactory.attachment(attachment=review_card)

        post_from_same_channel = False
        try:
            if teams_get_channel_id(turn_context.activity) == self._team_config["channel_id"]:
                post_from_same_channel = True
        except:
            pass

        if not post_from_same_channel:
            await turn_context.send_activity(MessageFactory.text("*Review task has been posted to the Teams'channel : )*"))

        await self._create_new_thread_in_channel(turn_context, self._team_config["channel_id"], message=submit_review_message)

    async def _send_help_card(self, turn_context: TurnContext, member: Optional[Union[TeamsChannelAccount, ChannelAccount]]=None):
        help_message = ""
        if member:
            help_message += "Don't panic, {} {}. ".format(member.given_name, member.surname)
        help_message += "Help info will be provided in the future : )"
        await turn_context.send_activity(MessageFactory.text(help_message))

    async def _send_task_group_card(self, turn_context: TurnContext):
        message = MessageFactory.attachment(
            attachment=CardFactory.adaptive_card(
                bot_utils.construct_group_info_card(self._team_config, self._saved_team_members)
            )
        )

        await turn_context.send_activity(message)

    async def _send_add_user_card(self, turn_context: TurnContext):
        current_user: ChannelAccount = turn_context.activity.from_property
        self._update_saved_members(current_user.as_dict())
        self._export_saved_team_members()

        greeting = "Hi, {}, you have been added to groups: General".format(current_user.name)

        for group_name, members in self._team_config.get("groups", {}).items():
            if current_user.name in members:
                greeting += ", " + group_name

        await turn_context.send_activity(MessageFactory.text(greeting))

    def _update_saved_members(self, new_member: Dict):
        for member in self._saved_team_members:
            if member["id"] == new_member["id"]:
                self._saved_team_members.remove(member)
                self._saved_team_members.append(new_member)
                return
        self._saved_team_members.append(new_member)
        

    async def _create_new_thread_in_channel(self, turn_context: TurnContext, teams_channel_id: str, message):
        params = ConversationParameters(
                                            is_group=True, 
                                            channel_data={"channel": {"id": teams_channel_id}},
                                            activity=message,
                                        )

        
        connector_client = await turn_context.adapter.create_connector_client(turn_context.activity.service_url)
        await connector_client.conversations.create_conversation(params)

    async def _delete_card_activity(self, turn_context: TurnContext):
        await turn_context.delete_activity(turn_context.activity.reply_to_id)

    def _load_team_config(self) -> Dict:
        try:
            with open(self._team_config_file, "r") as f_ptr:
                return json.load(f_ptr)
        except IOError:
            raise IOError("No team config file")

    def _export_saved_team_members(self):
        with open(self._team_member_file, "w+") as f_ptr:
            json.dump(self._saved_team_members, f_ptr)

    def _load_saved_team_members(self) -> List[Dict]:
        if os.path.exists(self._team_member_file):
            with open(self._team_member_file, "r") as f_ptr:
                members = json.load(f_ptr)
        if not members:
            members = []

        return members
