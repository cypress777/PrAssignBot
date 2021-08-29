import pymsteams


IN_CONNECTOR_URL = "https://wisetechglobal.webhook.office.com/webhookb2/58e4c36a-74bf-40e1-82f8-d67b0166899e@8b493985-e1b4-4b95-ade6-98acafdbdb01/IncomingWebhook/604cc1d8c74c4063a32c868cb985e957/0be6a71a-b827-4512-acd2-ad6ff5f453f6"
messenger = pymsteams.connectorcard(IN_CONNECTOR_URL)

messenger.text("hello world")

messenger.send()
