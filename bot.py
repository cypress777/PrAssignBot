import traceback

import connexion


def echo():
    data_packet = connexion.request.json

    try:
        return data_packet
    except Exception:
        stacktrace = traceback.format_exc()
        return stacktrace, 500
