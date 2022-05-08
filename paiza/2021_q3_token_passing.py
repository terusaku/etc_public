# https://paiza.jp/works/mondai/vantan_2021/vantan_2021__q3_token_passing
N, K = list(map(int, input().split(' ')))

terminal_spec = {}
for i in range(N):
    terminal = i + 1
    terminal_spec[terminal] = int(input())
base_terminal = 1
total_req_time = 0
for i in range(K):
    calling_t = int(input())
    interval = calling_t - base_terminal
    if interval == 0:
        req_time = sum(terminal_spec.values())
    elif interval > 0:
        req_time = 0
        for n in range(interval):
            req_time += terminal_spec[base_terminal + n ]
    elif interval < 0:
        req_time = sum(terminal_spec.values())
        for n in range(abs(interval)):
            req_time -= terminal_spec[base_terminal - n - 1]

    base_terminal = calling_t
    total_req_time += req_time


print(total_req_time)
