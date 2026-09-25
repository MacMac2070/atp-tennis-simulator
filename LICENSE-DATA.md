# Data licence

The MIT licence in [`LICENSE`](LICENSE) covers the code in this repository only.

The ATP match data this project works with was compiled by Jeff Sackmann (Tennis Abstract) and is
licensed separately under [CC BY-NC-SA 4.0](https://creativecommons.org/licenses/by-nc-sa/4.0/):
non-commercial use only, attribution required, share-alike.

- **Original source:** `github.com/JeffSackmann/tennis_atp`, withdrawn in 2026 and no longer online.
- **Mirror used here:** [github.com/Aneeshers/tennis-sackmann-archive](https://github.com/Aneeshers/tennis-sackmann-archive),
  redistributed under the same licence. `fetch_data.sh` pins it to commit `8373358` (June 2026);
  the data runs to tournaments starting 25 May 2026.

The full dataset is not included in this repository; `fetch_data.sh` downloads it. The files here
that are derived from it are shared under the same CC BY-NC-SA 4.0 licence:

- the model weights under `artifacts/models/`;
- the simulation outputs under `artifacts/simulations/`;
- the 12 sample rows in `verification/reports/atp_spot_check_sample.csv`, and the match-level
  figures quoted in the reports under `verification/`.

Some of those reports also quote a few figures from TennisMyLife and the official ATP website, for
comparison only. Full provenance: [`docs/data_provenance.md`](docs/data_provenance.md).
