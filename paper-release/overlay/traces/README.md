# Workload data

`demo/*.csv` contains the simulator's synthetic examples and test fixtures.

`alibaba/MS_588.csv` is the processed 721-window workload used by the IKT paper.
It derives from Alibaba's
[microservice trace v2021](https://github.com/alibaba/clusterdata/tree/master/cluster-trace-microservices-v2021).
The source pipeline aggregates incoming provider/HTTP call rates for MS_588
into per-minute request counts. The simulator export maps `time_tick + 1` to
`time_unit` and `total_requests` to `requests`.

The bundled file is the canonical input for reproducing this paper:
721 samples, 3,385,510 total requests, minimum 932, maximum 29,778.
Its checksum is included in the root `release-files.sha256` manifest.

Please cite the original dataset publication:

Shutian Luo et al., "Characterizing Microservice Dependency and Performance:
Alibaba Trace Analysis," Proceedings of the ACM Symposium on Cloud Computing,
2021, pp. 412–426. DOI: [10.1145/3472883.3487003](https://doi.org/10.1145/3472883.3487003).

This is third-party data. The simulator's MIT license applies to the project
code and does not grant additional rights to Alibaba's data. Refer to the
upstream dataset for its applicable terms.
