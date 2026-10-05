# Pilot3 confidence and startup diagnosis

Reproduce with `python examples/diagnose_pilot3.py` after diagnostic extraction using `--include-confidence`. These are diagnostic reruns, not a new evaluation. No settings were changed.

## pilot3_full_reps

Original measurements and replay attempts reproduced exactly (392 frames). First confirmed top: 0.113 seconds.

Failure counts by component (a frame may appear in multiple categories): {'ankle_visibility': 8}.

First 0.5 seconds: time / raw elbow / filtered elbow (degrees):

```text
0.000 / 139.6467321076587 / 139.6467321076587
0.013 / 142.85713308404857 / 140.12824059804186
0.047 / 152.78756495684243 / 144.51128119090035
0.080 / 137.40272538467917 / 142.1085409666947
0.113 / 140.13729093541244 / 141.4422450450979
0.147 / 138.1730743163923 / 140.31035936125096
0.180 / 140.08240489929275 / 140.2333092022644
0.213 / 139.21602391989325 / 139.88945985591667
0.247 / 140.6439928300876 / 140.1507019696905
0.280 / 142.1024401986971 / 140.8104027693733
0.313 / 141.7153330894072 / 141.1162753740655
0.347 / 142.315766456109 / 141.53157542913627
0.380 / 142.6559697050328 / 141.91162834399117
0.413 / 154.4654222631127 / 146.1548960959955
0.447 / 135.09087855015082 / 142.32419892377055
0.480 / 135.7427786755821 / 140.09963410444615
```

Unreliable frame timestamps and causes:

```text
6.683: ankle_visibility=0.600
6.783: ankle_visibility=0.462
10.318: ankle_visibility=0.545
10.352: ankle_visibility=0.560
10.952: ankle_visibility=0.535
11.218: ankle_visibility=0.582
11.252: ankle_visibility=0.592
11.885: ankle_visibility=0.554
```

## pilot3_shallow_reps

Original measurements and replay attempts reproduced exactly (291 frames). First confirmed top: 2.053 seconds.

Failure counts by component (a frame may appear in multiple categories): {}.

First 0.5 seconds: time / raw elbow / filtered elbow (degrees):

```text
0.000 / 132.80677888912214 / 132.80677888912214
0.020 / 133.10075949982576 / 132.87180717000197
0.053 / 133.77363134849725 / 133.17662987772206
0.087 / 134.55139902985084 / 133.65261649666047
0.120 / 133.18584192728946 / 133.49484351660135
0.153 / 133.4492002218001 / 133.47941577243307
0.187 / 135.0194713254111 / 134.01262953745263
0.220 / 133.32668817055736 / 133.78077668877083
0.253 / 131.88335870833583 / 133.13943650266268
0.287 / 129.0508606604962 / 131.72384801031646
0.320 / 132.6873036670082 / 132.04950257696495
0.353 / 130.9853104852188 / 131.68979840992694
0.387 / 129.13431464570994 / 130.8050127171449
0.420 / 128.98790749614366 / 130.19081879011787
0.453 / 127.1329138390252 / 129.15722611277576
0.487 / 125.5482778137274 / 127.90769916774097
```

Unreliable frame timestamps and causes:

```text
```

## pilot3_mixed

Original measurements and replay attempts reproduced exactly (502 frames). First confirmed top: 3.77 seconds.

Failure counts by component (a frame may appear in multiple categories): {'ankle_visibility': 21, 'no_pose': 2}.

First 0.5 seconds: time / raw elbow / filtered elbow (degrees):

```text
0.000 / 134.26420574836843 / 134.26420574836843
0.002 / 133.77668237886343 / 134.2521687534871
0.035 / 134.11367098828663 / 134.20535556660622
0.068 / 136.47025966696833 / 134.97090856137143
0.102 / 133.60070138438823 / 134.49650143606792
0.135 / 138.14292511060424 / 135.7290174458088
0.168 / 138.3160916202635 / 136.60346611743995
0.202 / 138.10032360422272 / 137.12172340671876
0.235 / 138.22225994219772 / 137.49371224300094
0.268 / 136.72266738774363 / 137.23309383626744
0.302 / 138.82770268599273 / 137.78519560094168
0.335 / 136.96904357763822 / 137.50933066453058
0.368 / 137.30882338144147 / 137.44155783873342
0.402 / 138.5852907832799 / 137.83755274187783
0.435 / 139.76552766624147 / 138.4892213829222
0.468 / 141.2194091206856 / 139.4120434125975
```

Unreliable frame timestamps and causes:

```text
2.503: ankle_visibility=0.574
2.537: ankle_visibility=0.561
2.570: ankle_visibility=0.562
2.603: ankle_visibility=0.551
2.637: ankle_visibility=0.511
2.837: ankle_visibility=0.420
2.870: ankle_visibility=0.389
3.203: ankle_visibility=0.594
8.272: ankle_visibility=0.535
8.538: ankle_visibility=0.571
8.805: ankle_visibility=0.566
8.838: ankle_visibility=0.559
8.938: ankle_visibility=0.578
9.005: ankle_visibility=0.582
12.440: ankle_visibility=0.579
12.940: ankle_visibility=0.593
12.973: ankle_visibility=0.584
14.575: ankle_visibility=0.571
15.042: no_pose
15.075: no_pose
15.175: ankle_visibility=0.485
15.208: ankle_visibility=0.422
15.308: ankle_visibility=0.494
```

These scores indicate model confidence, not landmark accuracy. A missing/multiple-pose result is distinct from a low score on one joint. Timestamped manual labels are still required to assign misses to particular repetitions.
