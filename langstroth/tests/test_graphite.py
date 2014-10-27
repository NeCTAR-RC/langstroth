import mock

from langstroth import graphite


def test_target():
    target = graphite.Target("test.az.something")
    assert str(target) == 'test.az.something'

    # Test chaining
    assert isinstance(target, graphite.Target)


def test_target_alias():
    target = graphite.Target("test.az.something").alias('name1')
    assert str(target) == 'alias(test.az.something, "name1")'

    # Test chaining
    assert isinstance(target, graphite.Target)


def test_target_derivitave():
    target = graphite.Target("test.az.something").derivative()
    assert str(target) == 'derivative(test.az.something)'

    # Test chaining
    assert isinstance(target, graphite.Target)


def test_target_smartSummarise():
    target = graphite.Target("test.az.something")
    assert str(target.smartSummarize('1d')) \
        == 'smartSummarize(test.az.something, "1d", "avg")'

    assert str(target.smartSummarize('1d', 'sum')) \
        == 'smartSummarize(test.az.something, "1d", "sum")'

    assert str(target.smartSummarize(None)) \
        == 'test.az.something'

    # Test chaining
    assert isinstance(target, graphite.Target)


@mock.patch('langstroth.graphite.requests.get')
def test_get(mock_get):
    response = graphite.get(from_date='-1year')
    mock_get.assert_called_with(
        'http://graphite.dev.rc.nectar.org.au/render/?format=json&from=-1year')
    assert response == mock_get()


@mock.patch('langstroth.graphite.requests.get')
def test_get_target(mock_get):
    target = graphite.Target("test.az.something").alias("foo")
    response = graphite.get(from_date='-1year', targets=[target])
    mock_get.assert_called_with(
        'http://graphite.dev.rc.nectar.org.au/render/'
        '?format=json'
        '&target=alias%28test.az.something%2C+%22foo%22%29'
        '&from=-1year')
    assert response == mock_get()


@mock.patch('langstroth.graphite.requests.get')
def test_get_targets(mock_get):
    targets = [graphite.Target("test.az.something").alias("foo"),
               graphite.Target("test.az.something_else").alias("bar")]
    response = graphite.get(from_date='-1year', targets=targets)
    mock_get.assert_called_with(
        'http://graphite.dev.rc.nectar.org.au/render/'
        '?format=json'
        '&target=alias%28test.az.something%2C+%22foo%22%29'
        '&target=alias%28test.az.something_else%2C+%22bar%22%29'
        '&from=-1year')
    assert response == mock_get()


def test_fill_null_datapoints():
    data = [{"datapoints": [
        [None, 1324130400],
        [1.0, 1324216800],
        [3.0, 1325599200],
        [None, 1413208800]]}]
    result = graphite.fill_null_datapoints(data)

    assert result == [{"datapoints": [
        [0.0, 1324130400],
        [1.0, 1324216800],
        [3.0, 1325599200],
        [3.0, 1413208800]]}]
