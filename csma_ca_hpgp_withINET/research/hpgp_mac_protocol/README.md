# Research Results and Metrics

## Log Folder Naming
- Stored under `results/log/`
- Format: `HHMMSS_DD_MM_YYYY_ev<EVs>_evse<EVSEs>`
  - Example: `223015_20_09_2025_ev1_evse1`

## Summary (summary.csv)
Columns:
- run: unique run id
- numEvs: number of EV nodes
- seed: random seed
- repeat: repetition index (currently 1)
- status: OK if scalar (.sca) exists, else ERR
- dcDeadlineMissRate: fraction of DC responses exceeding 100ms airtime
- DcDeadlineMissCount: count of such deadline misses
- DcReqCnt: number of DC_REQUEST sent by EVs (sum over EVs)
- DcResCnt: number of DC_RESPONSE received by EVs (sum over EVs)
- DcAirtimeAvg: average EV-side airtime (request→response) in seconds
- DcAirtimeP95: 95th percentile EV-side airtime in seconds
- dcReqDelayRate: fraction of EV DC request inter-send intervals exceeding 100ms after SLAC_DONE
- slacDoneRate: fraction of EVs that completed SLAC

## Definitions
- DC Airtime: time from EV sending DC_REQUEST to EV receiving DC_RESPONSE.
- Deadline Miss (100ms): airtime > 0.1 seconds.
- Request Delay Rate: after SLAC completes, EV attempts to issue DC_REQUEST every 100ms. If actual send interval (previous request to next request) exceeds 100ms due to MAC contention, it counts as a delay.

## Notes
- Metrics are observational only and do not change protocol behavior.
- Legacy `results/summary.csv` is replaced by this schema.
