from langstroth import graphite


class GraphiteTimeSeries(object):

    def get_data(self, targets, granularity, date_from):

        targets = [graphite.Target(target).summarize(granularity).alias(alias)
                   for alias, target in targets]

        req = graphite.get(from_date=date_from, targets=targets)
        # data = graphite.fill_null_datapoints(req.json())
        return req.json()
