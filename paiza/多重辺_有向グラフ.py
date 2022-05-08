# https://paiza.jp/works/mondai/graph_input_problems/graph_input_problems__loops_multiple_edges_boss
N, M = list(map(int, input().split(' ')))

lines = []
for m in range(M):
    line = list(map(int, input().split(' ')))
    lines.extend([line])

def compare_links(link, target_lines):
    count_double = 0
    for i in target_lines:
        if set(link) == set(i):
            count_double += 1
            return link
    else:
        if count_double == 0:
            return []
            

result_links = []
shrink_result = []
# print(lines)
for i, link in enumerate(lines):
    if (i + 1) < len(lines):
        target_lines = lines[i+1:]
        # print(link, target_lines)
        result_link  = compare_links(link, target_lines)
        # print(result_link)
        if result_link:
            result_link.sort()
            result_links.extend([result_link])

# print(result_links)
if result_links:
    shrink_result = list(map(list, set(map(tuple, result_links))))
# print(shrink_result)

result_counts = len(shrink_result)
print(result_counts)
if result_counts > 0:
    for i in shrink_result:
        print(' '.join(map(str, i)))
