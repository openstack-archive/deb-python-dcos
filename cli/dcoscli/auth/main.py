import os
import docopt

import dcoscli
from dcos import auth, cmds, config, emitting, http, util
from dcos.errors import DCOSException
from dcoscli import tables
from dcoscli.subcommand import default_command_info, default_doc
from dcoscli.util import decorate_docopt_usage


emitter = emitting.FlatEmitter()
logger = util.get_logger(__name__)


def main(argv):
    try:
        return _main(argv)
    except DCOSException as e:
        emitter.publish(e)
        return 1


@decorate_docopt_usage
def _main(argv):
    args = docopt.docopt(
        default_doc("auth"),
        argv=argv,
        version='dcos-auth version {}'.format(dcoscli.version))

    http.silence_requests_warnings()

    return cmds.execute(_cmds(), args)


def _cmds():
    """
    :returns: all the supported commands
    :rtype: list of dcos.cmds.Command
    """

    return [
        cmds.Command(
            hierarchy=['auth', 'list-providers'],
            arg_keys=[],
            function=_list_providers),

        cmds.Command(
            hierarchy=['auth', 'login'],
            arg_keys=['--password', '--password-env', '--password-file',
                      '--provider', '--username', '--service-key'],
            function=_login),

        cmds.Command(
            hierarchy=['auth', 'logout'],
            arg_keys=[],
            function=_logout),

        cmds.Command(
            hierarchy=['auth'],
            arg_keys=['--info'],
            function=_info),
    ]


def _info(info):
    """
    :param info: Whether to output a description of this subcommand
    :type info: boolean
    :returns: process status
    :rtype: int
    """

    emitter.publish(default_command_info("auth"))
    return 0


def _list_providers(json_):
    """
    :returns: providers available for configured cluster
    :rtype: dict
    """

    providers = auth.get_providers()
    if providers or json_:
        emitting.publish_table(
            emitter, providers, tables.auth_providers_table, json_)
    else:
        raise DCOSException("No providers configured for your cluster")


def _get_password(password_str, password_env, password_file):
    """
    Get password for authentication

    :param password_str: password
    :type password_str: str
    :param password_env: name of environment variable with password
    :type password_env: str
    :param password_file: path to file with password
    :type password_file: bool
    :returns: password or None if no password specified
    :rtype: str | None
    """

    password = None
    if password_str:
        password = password_str
    elif password_env:
        password = os.environ.get(password_env)
    elif password_file:
        password = util.read_file(password_file)
    return password


def _login(password_str, password_env, password_file,
           provider, username, service_key):
    """
    :returns: process status
    :rtype: int
    """

    dcos_url = config.get_config_val("core.dcos_url")
    if dcos_url is None:
        msg = ("Please provide the url to your DC/OS cluster: "
               "`dcos config set core.dcos_url`")
        raise DCOSException(msg)

    # every call to login will generate a new token if applicable
    _logout()

    password = _get_password(password_str, password_env, password_file)
    if provider is None:
        if password and username:
            auth.get_dcostoken_by_dcos_uid_password_auth(
                dcos_url, username, password)
        else:
            auth.header_challenge_auth(dcos_url)
    else:
        raise DCOSException("Providers interface not implemented")

    emitter.publish("Login successful!")
    return 0


def _logout():
    """
    Logout the user from dcos acs auth or oauth

    :returns: process status
    :rtype: int
    """

    if config.get_config_val("core.dcos_acs_token") is not None:
        config.unset("core.dcos_acs_token")
    return 0
