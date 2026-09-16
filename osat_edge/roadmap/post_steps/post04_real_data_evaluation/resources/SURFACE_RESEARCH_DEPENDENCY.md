# Optional surface-research dependency

`convert-keyence-files` 0.1.0 is used only for offline inspection of the TUHH
Keyence VK7 files. Snapshot 4 pins commit
`36e1eb9f550a41f5be2369de125ec51338f54d9e`; that revision declares the
[Unlicense](https://github.com/nulltyto/convert_keyence_files/blob/36e1eb9f550a41f5be2369de125ec51338f54d9e/LICENSE).

It is absent from root runtime requirements. Install it only for the optional
surface audit:

```powershell
.venv\Scripts\python -m pip install -r osat_edge\roadmap\post_steps\post04_real_data_evaluation\resources\requirements-surface-research.txt
```

The evaluator checks both distribution version and the installed VCS commit
from `direct_url.json`. A missing or differently installed parser leaves the
verified dataset at `INSPECTED_NOT_EXECUTABLE`; it does not fabricate a
conversion. The GPL `surfalize` package is intentionally not a dependency.
