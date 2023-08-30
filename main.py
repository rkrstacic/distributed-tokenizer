import json

import seaborn as sns
import matplotlib.pyplot as plt
import statistics

from google.colab import drive
from collections import defaultdict
from collections import Counter

from getting_unk_tokens import SaveUnknownTokensService
from simulation_v2 import Simulation


def get_user_unk_tokens_optimized(user):
    joined_comments = " ".join(all_comments[user])
    word_counts = Counter(joined_comments.split())

    return [word_counts[unk] for unk in all_unk_tokens]


def bool_arr_to_int(arr):
    return int("".join(map(lambda x: str(int(x)), arr)), 2)


def matching(source_user: int, target_user: int):
    source_user_shift = 2 ** (len(bin(source_user)) - 2) + source_user
    return bin(source_user_shift & target_user).count("1") / bin(source_user).count("1")


def plot_grafs():
    matrix = list(list(matching(user_j, user_i) for user_i in _users) for user_j in _users)
    ax = sns.heatmap(matrix)
    plt.show()

    nba_users_unk_counts = [bin(user).count("1") for user in _users[1:100]]
    politics_users_unk_counts = [bin(user).count("1") for user in _users[101:200]]

    fig, ax = plt.subplots()
    indices = range(len(nba_users_unk_counts))
    ax.plot(indices, nba_users_unk_counts)

    ax.set_xlabel('X-axis')
    ax.set_ylabel('Y-axis')
    ax.set_title('NBA Plot')

    plt.show()

    fig, ax = plt.subplots()
    indices = range(len(politics_users_unk_counts))
    ax.plot(indices, politics_users_unk_counts)

    ax.set_xlabel('X-axis')
    ax.set_ylabel('Y-axis')
    ax.set_title('Politics Plot')

    plt.show()

    print(sum(nba_users_unk_counts) / 100)
    print(sum(politics_users_unk_counts) / 100)
    print(statistics.median(nba_users_unk_counts))
    print(statistics.median(politics_users_unk_counts))


def get_and_save_unk_tokens():
    with open("nba.txt") as n, open("politics.txt") as p:
        nba_comments = " ".join(json.loads(row)["comment"] for row in n)
        politics_comments = " ".join(json.loads(row)["comment"] for row in p)

    service = SaveUnknownTokensService("vocab.txt", "small_vocab.txt")
    service.tokenize_corpus(nba_comments + ' ' + politics_comments)
    # service.save_small_vocab()
    service.prepare_tokens()
    service.find_unknown_tokens()
    service.save_unknown_tokens("unknown_tokens.txt")


def simulation(steps, users, all_unk_tokens):
    simulation = Simulation(users, all_unk_tokens)
    simulation.clusters, simulation.cluster_user = simulation.get_better_distributed_clusters(5, 60)
    simulation.load_all_tokens_user_count()

    simulation.load_clusters()
    print("Initial array", simulation.cluster_user_status())

    for i in range(steps):
        simulation.simulate(100, 0)
        print("Loop", i)
        cus = simulation.cluster_user_status()
        gp = simulation.get_purities()

        print(list(map(lambda x: " " * (5 - len(str(x))) + str(x), cus)), "Clusters over 30 users:",
              len(list(filter(lambda x: x > 30, cus))))
        print(list(map(lambda x: " " * (5 - len(str(x[1]))) + (str(x[1]) if cus[x[0]] > 30 else (" " * len(str(x[1])))),
                       enumerate(gp))))
        print()


if __name__ == '__main__':
    drive.mount('/content/drive')

    with open('unknown_tokens.txt', 'r') as n:
        all_unk_tokens = n.read().split()

    with open("nba.txt") as n, open("politics.txt") as p:
        nba_comments = defaultdict(list)
        politics_comments = defaultdict(list)

        for row in n:
            nba_comments[json.loads(row)['author']].append(json.loads(row)['comment'])

        for row in p:
            politics_comments[json.loads(row)['author']].append(json.loads(row)['comment'])

    all_comments = nba_comments.copy()
    all_comments.update(politics_comments)

    rels = {user: get_user_unk_tokens_optimized(user) for user in [i for i in all_comments]}
    _users = list(bool_arr_to_int(list(map(bool, i))) for i in rels.values())

    # get_and_save_unk_tokens()
    # simulation(1000, _users, all_unk_tokens)
