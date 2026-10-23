# Interrupted Run

This run stopped while serializing the first model attempt: the installed
Transformers image processor stores `size` as a `SizeDict`, not a JSON object.
The metadata serializer was changed to use `dict(size)` and a regression test
was added. This directory contains no completed experiment or usable scores.
The rerun uses a separate `coordinate_ablation_v2` directory.
