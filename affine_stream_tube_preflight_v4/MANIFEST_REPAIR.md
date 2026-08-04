# Affine stream-tube v4 payload-manifest repair

Workflow `30878715782` failed before candidate decoding, compilation, or scoring because the committed `part01.b64` had SHA-256 `47eada13f294fccdb7c6b8e0a7381534f6292dad51f1b5e2cb30600bc479918b`, while the workflow manifest incorrectly expected `a088c115ab3dae39dfae2e66688e58d30efcfacd57285b9067383b8d06a88166`.

The failure artifact `8880457039` independently recorded the actual committed file hash. No decoded source hash, meteor window, score, comparator, or endpoint was observed.

This repair changes only:

1. the expected `part01.b64` file hash to the artifact-recorded committed hash;
2. the workflow trigger and checkout ref needed to execute this stacked repair branch.

The decoded candidate must still match the previously frozen SHA-256 `7ec195a34fa286129f01d181b7a8365623a0266d76c153a155d98d220cc833f3`. Every source byte, physical statistic, data input, seed, calibration count, comparator, fold, threshold, gate, and blind interval remains unchanged.

If the decoded source fails its frozen hash or any scientific gate fails, this formulation is killed without another payload or method repair.