from typing import Any, List, Optional, Union, Dict
import json
import os
import pathlib
import random
from botbuilder.core import CardFactory, TurnContext, MessageFactory
from botbuilder.core.teams import TeamsActivityHandler, teams_get_channel_id
from botbuilder.schema import ConversationParameters, ChannelAccount
from botbuilder.schema.teams import (
    TeamInfo,
    TeamsChannelAccount,
    MessagingExtensionActionResponse,
    MessagingExtensionAction,
)
import copy

import bots.card_utils as bot_utils


PR_CHANNEL_ID = "19:1a214a2780304f409bc7e200a70f1c86@thread.tacv2"
TEAM_ID = "19:6f50da8c44b34e9bb039b328cd8b5026@thread.tacv2"

class PrAssignBot(TeamsActivityHandler):
    def __init__(self, app_id: str, app_password: str):
        self._app_id = app_id
        self._app_password = app_password
        self._TEAM_CONFIG: Dict[str, Any] = self._load_team_config()
        self._general_task_group: List[str] = self._get_general_task_group(self._TEAM_CONFIG["groups"])
        self._added_team_members: List[ChannelAccount] = []

    @staticmethod
    def _get_general_task_group(groups: Dict[str, List]) -> List[str]:
        members = []
        for group in groups.values():
            members.extend(group)

        return list(set(members))

    async def on_teams_members_added(  # pylint: disable=unused-argument
        self,
        teams_members_added: List[TeamsChannelAccount],
        team_info: TeamInfo,
        turn_context: TurnContext,
    ):
        for member in teams_members_added:
            if member.id != turn_context.activity.recipient.id:
                await turn_context.send_activity(
                    f"Welcome to the team { member.given_name } { member.surname }. "
                )

    async def on_teams_messaging_extension_submit_action_dispatch(
        self, turn_context: TurnContext, action: MessagingExtensionAction
    ) -> MessagingExtensionActionResponse:
        if action.command_id == "submitPR":
            group_name = self._get_valid_group_name(action.data.get("TaskGroup", ""))
            if group_name:
                await self._submit_pr(turn_context, action.data)
            else:
                await self._select_group_for_pr(turn_context, action.data)
            return MessagingExtensionActionResponse()
        raise NotImplementedError(f"Unexpected action.command_id {action.command_id}.")

    async def _select_group_for_pr(
        self,
        turn_context: TurnContext,  # pylint: disable=unused-argument
        data: Dict,
    ):
        reviewee: Union[ChannelAccount, TeamsChannelAccount] = turn_context.activity.from_property

        select_group_message = MessageFactory.attachment(
            attachment=CardFactory.adaptive_card(
                bot_utils.construct_select_group_card(
                    data["WI"],
                    data["PrLink"],
                    data["Description"],
                    reviewee,
                    self._TEAM_CONFIG["groups"],
                )
            )
        )
        await turn_context.send_activity(select_group_message)

    def _get_valid_group_name(self, group_name: str) -> Optional[str]:
        for name in self._TEAM_CONFIG["groups"]:
            if name.lower() == group_name.strip().lower():
                return name
        return None

    # TODO: count task assigned to each reviewers, add weight to them
    def _assign_reviewers(self, reviewee: str, task_group_name: str, number_of_reviewers: int=-1):
        task_group_name = self._get_valid_group_name(task_group_name)

        if not task_group_name or len(self._TEAM_CONFIG["groups"][task_group_name]) == 0:
            group = self._general_task_group
        else:
            group = self._TEAM_CONFIG["groups"][task_group_name]

        new_group_without_reviewee = copy.deepcopy(group)
        if reviewee in group:
            new_group_without_reviewee.remove(reviewee)

        if number_of_reviewers == -1:
            number_of_reviewers = max(1, len(new_group_without_reviewee) / 3)

        reviewers = []
        while number_of_reviewers > 0 and len(new_group_without_reviewee) > 0:
            reviewer = random.choice(new_group_without_reviewee)
            reviewers.append(reviewer)

            new_group_without_reviewee.remove(reviewer)
            number_of_reviewers -= 1

        return reviewers

    async def _submit_pr(
        self,
        turn_context: TurnContext,  # pylint: disable=unused-argument
        data: Dict,
    ):
        reviewee: Union[ChannelAccount, TeamsChannelAccount] = turn_context.activity.from_property

        reviewers = self._assign_reviewers(reviewee.name, data.get("TaskGroup", ""))

        submit_pr_message = MessageFactory.attachment(
            attachment=CardFactory.adaptive_card(
                bot_utils.construct_pr_submit_form(
                    data["WI"],
                    data["PrLink"],
                    data["Description"],
                    reviewee,
                    reviewers,
                    self._added_team_members,
                )
            )
        )

        post_from_same_channel = False
        try:
            if teams_get_channel_id(turn_context.activity) == PR_CHANNEL_ID:
                post_from_same_channel = True
        except:
            pass

        if not post_from_same_channel:
            await turn_context.send_activity(MessageFactory.text("Pr review request has been updated to the channel"))

        await self._create_new_thread_in_channel(turn_context, PR_CHANNEL_ID, message=submit_pr_message)

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
            value = turn_context.activity.value

            if value.get("action", None):
                if "deletethiscard" in value["action"].strip().lower():
                    await self._delete_card_activity(turn_context)
                    return

                if "submitpr" in value["action"].strip().lower():
                    await self._submit_pr(turn_context, value)
                    return

        await self._send_help_card(turn_context)
        return

    async def _send_help_card(self, turn_context: TurnContext):
        await turn_context.send_activity(MessageFactory.text("No help info"))

    async def _send_task_group_card(self, turn_context: TurnContext):
        message = MessageFactory.attachment(
            attachment=CardFactory.adaptive_card(
                bot_utils.construct_group_info_card(self._TEAM_CONFIG)
            )
        )

        await turn_context.send_activity(message)

    async def _send_add_user_card(self, turn_context: TurnContext):
        current_user: ChannelAccount = turn_context.activity.from_property
        self._added_team_members.append(current_user)

        greeting = "Hi, {}, you have been added to groups: General".format(current_user.name)

        for group_name, members in self._TEAM_CONFIG.get("groups", {}).items():
            if current_user.name in members:
                greeting += ", " + group_name

        await turn_context.send_activity(MessageFactory.text(greeting))

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
        file_path = os.path.join(os.path.dirname(__file__), "team_config.json")
        with open(file_path, "r") as f_ptr:
            return json.load(f_ptr)
