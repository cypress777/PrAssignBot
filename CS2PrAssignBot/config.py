#!/usr/bin/env python3
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

import os


class DefaultConfig:
    """ Bot Configuration """

    PORT = 3978
    APP_ID = os.environ.get("MicrosoftAppId", "4baa95bd-5c4d-498b-98d1-d57c74211e7e")
    APP_PASSWORD = os.environ.get("MicrosoftAppPassword", "QNr%[BwgYA1E[9hGW4x1/)]msBjE")
