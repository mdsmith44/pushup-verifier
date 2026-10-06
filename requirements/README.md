# Python dependencies

| File | Purpose |
|---|---|
| `video.txt` | Pose extraction dependencies |
| `app.txt` | Local upload application, including `video.txt` |
| `app.lock.txt` | Tested installed dependency snapshot for Linux/Python 3.12 |
| `aws.txt` | AWS SDK for the cloud worker |
| `learning.txt` | Dependencies for early learning exercises |

For the complete local application:

```bash
python -m pip install -r requirements/app.lock.txt
```

For the cloud worker, also install:

```bash
python -m pip install -r requirements/aws.txt
```

The lock file is an installed environment snapshot, not a cross-platform or hash-verified lock. `examples/lock_app_dependencies.py` regenerates it from the relevant installed environment. The decision-engine tests and synthetic CSV replay use only the Python standard library.
