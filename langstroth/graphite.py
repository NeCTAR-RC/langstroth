
# Addressing the history components
# within a 2-member data-point array.
VALUE_INDEX = 0
TIMESTAMP_INDEX = 1


def filter_null_datapoints(response_data):
    """
    Example Graphite response =
    [
        {
            "target": "Cumulative",
            "datapoints": [
                [null, 1324130400],
                [0.0, 1324216800],
                [0.0, 1324303200],
                [2.0, 1325512800],
                [3.0, 1325599200],
                [null, 1413208800]
            ]
        },
        {
            "target": "Frequency",
            "datapoints": [
                [null, 1324130400],
                [null, 1324216800],
                [0.0, 1324303200],
                [2.0, 1325512800],
                [null, 1325599200],
                [null, 1413208800]
            ]
        }
    ]

    Remove any datapoint with a null value component.
    """

    for data_series in response_data:
        data_points = data_series['datapoints']
        data_series['datapoints'] = [datapoint
                                     for datapoint in data_points
                                     if datapoint[VALUE_INDEX] is not None]
    return response_data
