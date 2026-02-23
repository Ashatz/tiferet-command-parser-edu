from tiferet import App

# Create new app (manager) instance.
app = App(dict(
    app_repo_params=dict(
        app_config_file='config.yml',
    )
))

# Load the CLI app instance.
cli = app.load_interface('compiler_cli')

# Run the CLI app.
if __name__ == '__main__':
    cli.run()
