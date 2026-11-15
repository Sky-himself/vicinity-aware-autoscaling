# Workload provenance

Synthetic CSVs under `demo/` exercise simulation and policy mechanics.
The eight processed Alibaba CSVs contain one-minute request-count series from
[Alibaba's microservice trace v2021](https://github.com/alibaba/clusterdata/tree/master/cluster-trace-microservices-v2021).
Input CSVs use `time_unit,requests`; the development pipeline exported
`time_tick + 1` as the window index and `total_requests` as the count.

Dataset reference: Shutian Luo et al., "Characterizing Microservice Dependency
and Performance: Alibaba Trace Analysis," SoCC 2021, pp. 412–426,
[DOI 10.1145/3472883.3487003](https://doi.org/10.1145/3472883.3487003).

Third-party dataset rights remain with the upstream data providers. Campaign
provenance records checksums of the exact processed inputs used. These bundled
processed series enable replay; full raw-data preparation is not packaged here.
