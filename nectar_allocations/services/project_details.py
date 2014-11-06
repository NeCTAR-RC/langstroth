from langstroth import graphite
from datetime import date


'''
A project details service.

Including:
    the latest core and usage counts.

Project usage counts are obtained
by querying the Graphite service end-point.
'''


def find_current_project_resource_usage(tenancy_id):
    '''
    Retrieve the last daily value for the project/tenancy
    usage of instances and cores.
    '''
    today = date.today()
    todayStr = today.strftime('%Y%m%d')

    targets = []

    targetName = "tenant.%s.total_instances" % tenancy_id
    targets.append(graphite.Target(targetName)
                   .smartSummarize('1d', 'max')
                   .alias('instance_count'))

    targetName = "tenant.%s.used_vcpus" % tenancy_id
    targets.append(graphite.Target(targetName)
                   .smartSummarize('1d', 'max')
                   .alias('core_count'))

    response = graphite.get(from_date=todayStr, targets=targets)
    return graphite.filter_null_datapoints(response.json())
