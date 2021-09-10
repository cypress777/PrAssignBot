from datetime import date
from typing import List
from botbuilder.core import CardFactory, TurnContext, MessageFactory
from botbuilder.core.teams import TeamsActivityHandler, TeamsInfo, teams_get_channel_id
from botbuilder.schema import CardAction, HeroCard, Mention, ConversationParameters, ChannelAccount
from botbuilder.schema.teams import (
    TeamInfo,
    TeamsChannelAccount,
    MessagingExtensionActionResponse,
    MessagingExtensionAction,
    MessagingExtensionAttachment,
    MessagingExtensionResult,
)
from botbuilder.schema._connector_client_enums import ActionTypes

import bots.utils as bot_utils


PR_CHANNEL_ID = "19:1a214a2780304f409bc7e200a70f1c86@thread.tacv2"

class PrAssignBot(TeamsActivityHandler):
    def __init__(self, app_id: str, app_password: str):
        self._app_id = app_id
        self._app_password = app_password

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
            return await self._submit_pr(turn_context, action)

        raise NotImplementedError(f"Unexpected action.command_id {action.command_id}.")

    async def _submit_pr(
        self,
        turn_context: TurnContext,  # pylint: disable=unused-argument
        action: MessagingExtensionAction,
    ) -> MessagingExtensionActionResponse:
        current_time = date.today().strftime("%d/%m/%Y")
        reviewee: ChannelAccount = turn_context.activity.from_property

        message = MessageFactory.attachment(
            attachment=CardFactory.adaptive_card(
                bot_utils.construct_pr_submit_form(
                    action.data["WI"],
                    action.data["PrLink"],
                    action.data["Description"],
                    current_time,
                    reviewee,
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

        await self._create_new_thread_in_channel(turn_context, PR_CHANNEL_ID, message=message)

        return MessagingExtensionActionResponse()

    async def on_message_activity(self, turn_context: TurnContext):
        TurnContext.remove_recipient_mention(turn_context.activity)
        if turn_context.activity.text:
            text = turn_context.activity.text.strip().lower()

            if "show" in text:
                await self._send_task_group_card(turn_context, True)
                return

        if turn_context.activity.value:
            value = turn_context.activity.value
            
            if value["action"]:
                if "deletethiscard" in value["action"].strip().lower():
                    await self._delete_card_activity(turn_context)
                    return

        await self._send_help_card(turn_context, False)
        return

    async def _send_help_card(self, turn_context: TurnContext, isUpdate):
        await turn_context.send_activity(MessageFactory.text("No help info"))

    async def _send_task_group_card(self, turn_context: TurnContext, isUpdate):
        await turn_context.send_activity(MessageFactory.text("No task group info"))

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
