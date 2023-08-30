import math
import random
import bisect
import numpy as np

from numpy.random import randint


def binary_search(arr, target):
    index = bisect.bisect_left(arr, target)
    if index < len(arr) and arr[index] == target:
        return index
    else:
        return -1  # Target not found


def matching(source_user: int, target_user: int):
    source_user_shift = 2 ** (len(bin(source_user)) - 2) + source_user
    return bin(source_user_shift & target_user).count("1") / bin(source_user).count("1")


# Matching score of user x in regard to a cluster
def get_max_matching_score(_user, _clusters):
    matching_scores = [matching(_user, cluster) for cluster in _clusters]
    return max(matching_scores)


class Simulation:
    all_tokens_count = 0
    clusters = []
    clusters_copy = []
    all_tokens_user_count = []
    cluster_user = None

    def __init__(self, users, all_unk_tokens):
        self.users = users
        self.all_unk_tokens = all_unk_tokens
        self.all_tokens_count = len(all_unk_tokens)

    def load_all_tokens_user_count(self):
        all_tokens_user_count = [0] * self.all_tokens_count
        for user in self.users:
            user_bin = "0" * (self.all_tokens_count - len(bin(user)[2:])) + bin(user)[2:]
            for i in range(len(user_bin)):
                all_tokens_user_count[i] += int(user_bin[i])

        self.all_tokens_user_count = all_tokens_user_count

    def get_random_cluster(self):
        token_cluster_indices = [randint(0, 10) for _ in self.all_unk_tokens]

        clusters_count = 10
        clusters_arr = [list('0' * self.all_tokens_count) for _ in range(clusters_count)]

        for index, token_cluster_index in enumerate(token_cluster_indices):
            clusters_arr[token_cluster_index][index] = "1"

        return list(map(lambda cluster_arr: int(''.join(cluster_arr), 2), clusters_arr))

    # Matching score of user x in regard to a cluster
    def get_cluster_index_with_max_matching_score(self, _user):
        matching_scores = [matching(_user, cluster) for cluster in self.clusters]
        return np.argmax(matching_scores)

    def get_better_distributed_clusters(self, min_count=0, max_count=9999):
        while True:
            cluster_user = [list() for _ in range(10)]
            clusters = self.get_random_cluster()

            for index, user in enumerate(self.users):
                cluster = self.get_cluster_index_with_max_matching_score(user)
                cluster_user[cluster].append(index)

            if min(list(map(len, cluster_user))) >= min_count and max(list(map(len, cluster_user))) <= max_count:
                return clusters, cluster_user

    def get_x_tokens_not_in_cluster(self, _user, _cluster, x=100):
        tokens_int = _user & ~_cluster  # Exists on user and not in cluster
        tokens_cut = bin(tokens_int)[2:]
        missing_leading_zeroes = self.all_tokens_count - len(tokens_cut)
        tokens = "0" * missing_leading_zeroes + tokens_cut

        one_indices = [i for i, val in enumerate(tokens) if val == "1" and self.all_tokens_user_count[i] <= 10]

        return random.sample(one_indices, min(x, len(one_indices)))

    def get_new_clusters_after_transfering_token(self, cluster_from_index, cluster_to_index, token_to_transfer):
        # token transition from cluster to cluster
        temp_clusters = [i for i in self.clusters]
        temp_clusters[cluster_from_index] = temp_clusters[cluster_from_index] - (
                    2 ** (self.all_tokens_count - token_to_transfer - 1))
        temp_clusters[cluster_to_index] = temp_clusters[cluster_to_index] + (
                    2 ** (self.all_tokens_count - token_to_transfer - 1))
        return temp_clusters

    def user_propose_tokens(self, user, batch_size):
        cluster_index = self.get_cluster_index_with_max_matching_score(user)
        cluster = self.clusters[cluster_index]  # User cluster

        return self.get_x_tokens_not_in_cluster(user, cluster, batch_size)  # Tokens to transfer

    def user_vote(self, user, token_index, unk_tokens_cluster_map, min_increase=0):
        matching_score = get_max_matching_score(user, self.clusters)
        cluster_index = self.get_cluster_index_with_max_matching_score(user)

        new_clusters = self.get_new_clusters_after_transfering_token(unk_tokens_cluster_map[token_index], cluster_index,
                                                                token_index)
        new_matching_score = get_max_matching_score(user, new_clusters)

        if new_matching_score > matching_score + min_increase:
            return 1

        if new_matching_score < matching_score - min_increase:
            return -1

        return 0

    def save_clusters(self):
        self.clusters_copy = [i for i in self.clusters]

    def load_clusters(self):
        self.clusters = [i for i in self.clusters_copy]

    def cluster_user_status(self):
        cluster_user = [list() for _ in range(10)]

        for index, user in enumerate(self.users):
            cluster = self.get_cluster_index_with_max_matching_score(user)
            cluster_user[cluster].append(index)

        return list(map(len, cluster_user))

    def get_purities(self):
        purity_cluster_user = [list() for _ in range(10)]

        for index, user in enumerate(self.users):
            c = self.get_cluster_index_with_max_matching_score(user)
            purity_cluster_user[c].append(index)

        return list(map(lambda cluster: round(
            2 * abs(50 - sum(100 * list(map(lambda user: user <= (len(self.users) / 2), cluster))) / len(cluster)), 1),
                        purity_cluster_user))

    # Map to fetch cluster by token
    def get_unk_tokens_cluster_map(self):
        unk_tokens_cluster_map = [-1] * self.all_tokens_count
        for i, c in enumerate(self.clusters):
            one_indices = [j + self.all_tokens_count - len(bin(c)[2:]) for j, val in enumerate(bin(c)[2:]) if val == "1"]
            for index in one_indices:
                unk_tokens_cluster_map[index] = i

        return unk_tokens_cluster_map

    def vote(self, user, unk_tokens_cluster_map, batch_size, min_inc):
        proposed_tokens = self.user_propose_tokens(user, batch_size)

        votes = [0] * len(proposed_tokens)
        for _user in self.users:
            for i, proposed_token in enumerate(proposed_tokens):
                votes[i] += self.user_vote(_user, proposed_token, unk_tokens_cluster_map, min_inc)

        return proposed_tokens, votes

    def simulate(self, vote_batch_size, min_inc):
        user = random.choice(self.users)
        unk_tokens_cluster_map = self.get_unk_tokens_cluster_map()
        tokens, votes = self.vote(user, unk_tokens_cluster_map, vote_batch_size, min_inc)

        user_cluster_index = self.get_cluster_index_with_max_matching_score(user)
        for i in range(len(tokens)):
            if votes[i] > 0:
                unk_tokens_cluster_map = self.get_unk_tokens_cluster_map()
                self.clusters = self.get_new_clusters_after_transfering_token(unk_tokens_cluster_map[tokens[i]],
                                                                    user_cluster_index, tokens[i])


if __name__ == '__main__':
    users = []
    all_unk_tokens = []
    simulation = Simulation(users, all_unk_tokens)
    simulation.clusters, simulation.cluster_user = simulation.get_better_distributed_clusters(5, 60)
    simulation.load_all_tokens_user_count()

    simulation.load_clusters()
    print("Initial array", simulation.cluster_user_status())

    for i in range(1000):
        simulation.simulate(100, 0)
        print("Loop", i)
        cus = simulation.cluster_user_status()
        gp = simulation.get_purities()

        print(list(map(lambda x: " " * (5 - len(str(x))) + str(x), cus)), "Clusters over 30 users:", len(list(filter(lambda x: x > 30, cus))))
        print(list(map(lambda x: " " * (5 - len(str(x[1]))) + (str(x[1]) if cus[x[0]] > 30 else (" " * len(str(x[1])))), enumerate(gp))))
        print()
