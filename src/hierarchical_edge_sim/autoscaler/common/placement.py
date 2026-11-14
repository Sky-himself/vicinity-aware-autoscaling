"""Deterministic placement helpers shared by reference controllers."""

from __future__ import annotations

from hierarchical_edge_sim.env.api import Env


def home_cluster_id(env: Env, ms_id: str) -> str:
    """Return the application's owning cluster."""
    return env.get_app_owner_cluster_id(ms_id)


def rank_servers_for_spawn(env: Env, ms_id: str, cluster_id: str) -> list[str]:
    """Already-hosting servers first, then free CPU descending, then id."""
    ms = env.get_microservice(ms_id)
    hosting = {env.get_container(cid).server_id for cid in ms.container_ids}
    servers = list(env.get_cluster(cluster_id).server_ids)

    def key(sid: str) -> tuple[int, float, str]:
        free_cpu, _ = env.get_server_free(sid)
        already = 0 if sid in hosting else 1
        return (already, -free_cpu, sid)

    return sorted(servers, key=key)
