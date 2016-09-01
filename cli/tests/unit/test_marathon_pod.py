from mock import Mock, create_autospec

from dcos import marathon
import dcoscli.marathon.main as main

# Pod add function
# Arguments: file path of pod JSON
# Returns: exit code for CLI, or throws exceptions (see what existing code does)
# Side effects:
#   - Read contents of pod JSON file
#   - Send HTTP request with contents of file, and some other stuff


def test_add_invoked_successfully():
    _assert_add_invoked_successfully(pod_file_json={"arbitrary": "json"})
    _assert_add_invoked_successfully(pod_file_json=["more", "json"])


def _assert_add_invoked_successfully(pod_file_json):
    pod_file_path = "some/path/to/pod.json"
    resource_reader = {pod_file_path: pod_file_json}.__getitem__
    marathon_client = create_autospec(marathon.Client)

    pod = main.MarathonPodSubcommand(resource_reader, marathon_client)
    returncode = pod.add(pod_file_path)

    assert returncode == 0
    marathon_client.add_pod.assert_called_with(pod_file_json)


def test_add_propagates_file_read_errors():
    # file_reader throws some exception (check against actual reader code)
    pod = MarathonPodSubcommand(file_reader, marathon_client)

    try:
        pod.add(pod_file_path)
    except SomeException as e:
        # assert that the exception is as expected
        pass

    pass


def test_add_requires_json_file():
    # file_reader returns invalid JSON
    # test that we fail early -- is an exception propagated or do we print?
    pod = MarathonPodSubcommand(file_reader, marathon_client)

    # catch exception and assert?
    pod.add(pod_file_path)
    pass


def test_add_propagates_marathon_api_failure():
    # the marathon_client is configured to throw some exception
    # test that the error is reported -- an exception or do we print?
    pod = MarathonPodSubcommand(file_reader, marathon_client)
    pod.add(pod_file_path)
