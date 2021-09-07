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


CHANNEL_ID = "19:1a214a2780304f409bc7e200a70f1c86@thread.tacv2"
def CONFIG_FORM_CARD(WI: str, pr_link: str, description: str, current_time: str, reviewee: ChannelAccount): 
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
                CONFIG_FORM_CARD(action.data["WI"], action.data["PrLink"], action.data["Description"], current_time, reviewee)
            )
        )

        post_from_same_channel = True
        try:
            if teams_get_channel_id(turn_context) != CHANNEL_ID:
                post_from_same_channel = False
        except:
            post_from_same_channel = False

        if not post_from_same_channel:
            await turn_context.send_activity(MessageFactory.text("Pr review request has been updated to the channel"))

        await self._create_new_thread_in_channel(turn_context, CHANNEL_ID, message=message)

        return MessagingExtensionActionResponse()

    async def on_message_activity(self, turn_context: TurnContext):
        TurnContext.remove_recipient_mention(turn_context.activity)
        text = turn_context.activity.text.strip().lower()
        if "create" in text:
            teams_channel_id = teams_get_channel_id(turn_context.activity)
            print(turn_context.activity)
            print(teams_channel_id)
            message = MessageFactory.text("This will be the start of a new thread")
            await self._create_new_thread_in_channel(turn_context, teams_channel_id, message=message)
            # await self._send_pr_form_card(turn_context)
            return

        if "show" in text:
            await self._send_task_group_card(turn_context, True)
            return

        await self._send_help_card(turn_context, False)
        return

    async def _send_help_card(self, turn_context: TurnContext, isUpdate):
        buttons = [
            CardAction(
                type=ActionTypes.message_back,
                title="Message all members",
                text="messageallmembers",
            ),
            CardAction(type=ActionTypes.message_back, title="Who am I?", text="whoami"),
            CardAction(
                type=ActionTypes.message_back, title="Delete card", text="deletecard"
            ),
        ]
        card = HeroCard(
            title="Welcome Card", text="Click the buttons.", buttons=buttons
        )
        await turn_context.send_activity(
            MessageFactory.attachment(CardFactory.hero_card(card))
        )

    async def _send_task_group_card(self, turn_context: TurnContext, isUpdate):
        buttons = [
            CardAction(
                type=ActionTypes.message_back,
                title="Message all members",
                text="messageallmembers",
            ),
            CardAction(type=ActionTypes.message_back, title="Who am I?", text="whoami"),
            CardAction(
                type=ActionTypes.message_back, title="Delete card", text="deletecard"
            ),
        ]
        card = HeroCard(
            title="Welcome Card", text="Click the buttons.", buttons=buttons
        )
        await turn_context.send_activity(
            MessageFactory.attachment(CardFactory.hero_card(card))
        )

    async def _send_pr_form_card(self, turn_context: TurnContext, isUpdate):
        buttons = [
            CardAction(
                type=ActionTypes.message_back,
                title="Message all members",
                text="messageallmembers",
            ),
            CardAction(type=ActionTypes.message_back, title="Who am I?", text="whoami"),
            CardAction(
                type=ActionTypes.message_back, title="Delete card", text="deletecard"
            ),
        ]
        card = HeroCard(
            title="Welcome Card", text="Click the buttons.", buttons=buttons
        )
        await turn_context.send_activity(
            MessageFactory.attachment(CardFactory.hero_card(card))
        )

    async def _create_new_thread_in_channel(self, turn_context: TurnContext, teams_channel_id: str, message):
        params = ConversationParameters(
                                            is_group=True, 
                                            channel_data={"channel": {"id": teams_channel_id}},
                                            activity=message,
                                        )

        
        connector_client = await turn_context.adapter.create_connector_client(turn_context.activity.service_url)
        await connector_client.conversations.create_conversation(params)
