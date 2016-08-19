
def assert_same_elements(list1, list2):
    for element in list1:
        list2.remove(element)
    assert not list2
