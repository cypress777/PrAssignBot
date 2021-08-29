import connexion


if __name__ == '__main__':
    app = connexion.FlaskApp(__name__, specification_dir="")
    app.add_api("api.yml")
    app.run(port=3978)
