import glob
import pytest
import lizard


# @pytest.fixture(autouse=True, scope='session')
# def lizard_targets():
#     path = './*.py'
#     files = glob.glob(path)

#     return files


# @pytest.fixture(autouse=True, scope='session')
# def execute_lizard(lizard_targets):
#     targets = lizard_targets
#     results = []
#     for code in targets:
#         analysis = lizard.analyze_file(code)
#         for i in analysis.function_list:
#             result = {}
#             result['name'] = analysis.__dict__['filename'] + '.' + i.__dict__['name']
#             result['ccn'] = i.__dict__['cyclomatic_complexity'] 
#             result['nloc'] = i.__dict__['nloc']
#             results.append(result)
#     # print(results)
#     return results
