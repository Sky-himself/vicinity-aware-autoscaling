# Forecast checkpoints

These checkpoints and their adjacent JSON metadata were imported from the
private research development snapshot. Metadata specifies lookback, forecast
horizon, preprocessing, time encoding, and network architecture. Scenario YAML
selects the model directory for each service.

The checkpoints support CPU inference with the optional `tcn` dependency.
They were fitted on the same short Alibaba interval used for replay. They are
not held-out forecasting benchmarks. Complete training-data preparation and
training scripts remain in the separate development project and have not yet
been packaged in this artifact.

Campaign provenance records SHA-256 hashes of selected weights and metadata.
