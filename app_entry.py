import os
from streamlit.web import bootstrap

if __name__ == '__main__':
    os.chdir(os.path.dirname(__file__))

    flag_options = {
        'global.developmentMode': False,
        'browser.serverAddress': 'localhost',
    }

    bootstrap.load_config_options(flag_options=flag_options)
    flag_options['_is_running_with_streamlit'] = True
    bootstrap.run(
        './README.py',
        'streamlit run',
        [],
        flag_options
    )
