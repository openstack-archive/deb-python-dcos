import getpass
import sys
from six.moves import urllib
from six.moves.urllib.parse import urlparse

from dcos import config, http
from dcos.errors import DCOSAuthenticationException, DCOSException


def _get_auth_scheme(response):
    """Return authentication scheme requested by server for
       'acsjwt' (DC/OS acs auth) or 'oauthjwt' (DC/OS acs oauth) type

    :param response: requests.response
    :type response: requests.Response
    :returns: auth_scheme
    :rtype: str
    """

    if 'www-authenticate' in response.headers:
        auths = response.headers['www-authenticate'].split(',')
        scheme = next((auth_type.rstrip().lower() for auth_type in auths
                       if auth_type.rstrip().lower().startswith("acsjwt") or
                       auth_type.rstrip().lower().startswith("oauthjwt")),
                      None)
        if scheme:
            scheme_info = scheme.split("=")
            auth_scheme = scheme_info[0].split(" ")[0].lower()
            return auth_scheme
        else:
            msg = ("Server responded with an HTTP 'www-authenticate' field of "
                   "'{}', DC/OS only supports ['oauthjwt', 'acsjwt']".format(
                       response.headers['www-authenticate']))
            raise DCOSException(msg)
    else:
        msg = ("Invalid HTTP response: server returned an HTTP 401 response "
               "with no 'www-authenticate' field")
        raise DCOSException(msg)


def _get_oidc_token(dcos_url):
    """Get OIDC Token for OIDC implicit flow

    :param dcos_url: dcos cluster url
    :type dcos_url: str
    :returns: OIDC token from browser for oauth flow
    :rtype: str
    """

    oauth_login = 'login?redirect_uri=urn:ietf:wg:oauth:2.0:oob'
    url = urllib.parse.urljoin(dcos_url, oauth_login)
    msg = "\n{}\n\n    {}\n\n{} ".format(
          "Please go to the following link in your browser:",
          url,
          "Enter OpenID Connect ID Token:")
    sys.stderr.write(msg)
    sys.stderr.flush()
    token = sys.stdin.readline().strip()
    return token


def _get_dcostoken_by_post_with_creds(dcos_url, creds):
    """
    Get DC/OS Authentication token by POST to `acs/api/v1/auth/login`
    with specific credentials (either OIDC token or uid/password)

    :param dcos_url: url to cluster
    :type dcos_url: str
    :param creds: credentials to login endpoint
    :type creds: {}
    :returns: DC/OS Authentication Token
    :rtype: str
    """

    url = urllib.parse.urljoin(dcos_url, 'acs/api/v1/auth/login')
    response = http._request('post', url, json=creds)

    token = None
    if response.status_code == 200:
        token = response.json()['token']
        config.set_val("core.dcos_acs_token", token)
    return token


def _prompt_for_uid_password(username, hostname):
    """Get username/password for auth

    :param username: username user for authentication
    :type username: str
    :param hostname: hostname for credentials
    :type hostname: str
    :returns: username, password
    :rtype: str, str
    """

    if username is None:
        sys.stdout.write("{}'s username: ".format(hostname))
        sys.stdout.flush()
        username = sys.stdin.readline().strip()

    password = getpass.getpass("{}@{}'s password: ".format(username, hostname))

    return username, password


def get_dcostoken_by_dcos_uid_password_auth(
        dcos_url, username=None, password=None):
    """
    Get DC/OS Authentication by DC/OS uid password auth

    :param dcos_url: url to cluster
    :type dcos_url: str
    :param username: username to auth with
    :type username: str
    :param password: password to auth with
    :type password: str
    :returns: DC/OS Authentication Token
    :rtype: str
    """

    url = urlparse(dcos_url)
    hostname = url.hostname
    username = username or url.username
    password = password or url.password

    if password is None:
        username, password = _prompt_for_uid_password(username, hostname)
    creds = {"uid": username, "password": password}
    return _get_dcostoken_by_post_with_creds(dcos_url, creds)


def _get_dcostoken_by_oidc_implicit_flow(dcos_url):
    """
    Get DC/OS Authentication by OIDC implicit flow

    :param dcos_url: url to cluster
    :type dcos_url: str
    :returns: DC/OS Authentication Token
    :rtype: str
    """

    oidc_token = _get_oidc_token(dcos_url)
    creds = {"token": oidc_token}
    return _get_dcostoken_by_post_with_creds(dcos_url, creds)


def header_challenge_auth(dcos_url):
    """
    Triggers authentication using scheme specified in www-authenticate header.

    Raises exception if authentication fails.

    :param dcos_url: url to cluster
    :type dcos_url: str
    :rtype: None
    """

    # hit protected endpoint which will prompt for auth if cluster has auth
    endpoint = '/pkgpanda/active.buildinfo.full.json'
    url = urllib.parse.urljoin(dcos_url, endpoint)
    response = http._request('HEAD', url)
    auth_scheme = _get_auth_scheme(response)

    i = 0
    while i < 3 and response.status_code == 401:
        if auth_scheme == "oauthjwt":
            token = _get_dcostoken_by_oidc_implicit_flow(dcos_url)
        # auth_scheme == "acsjwt"
        else:
            token = get_dcostoken_by_dcos_uid_password_auth(dcos_url)

        if token is not None:
            response.status_code = 200
            return
        else:
            i += 1

    raise DCOSAuthenticationException(response)


def get_providers():
    """
    Returns dict of providers configured on cluster

    :returns: configured providers
    :rtype: {}
    """

    dcos_url = config.get_config_val("core.dcos_url")
    endpoint = '/auth/providers'
    url = urllib.parse.urljoin(dcos_url, endpoint)
    try:
        providers = http.get(url)
    except DCOSHTTPException as e:
        if e.status_code == 404:
            msg = "This command is not supported for your cluster"
            raise DCOSException(msg)
        else:
            raise
