# Data provenance

Original benchmark data and modeling reference: **Hasan Arslan**, available in
[the public source repository](https://github.com/harslan/isom-839/tree/1e2b0374818759215a61475fe5eeb3af000f8263/public/session-07/case).
Source revision: `1e2b0374818759215a61475fe5eeb3af000f8263`.

The five raw CSVs retain their original bytes. The project is a retail benchmark
with illustrative inputs, not evidence of a live retailer deployment. The
forecasts are supplied data, not a learned model produced by this repository.
Source credit is retained; no new license is imposed on third-party data.
Public accessibility alone does not establish redistribution or commercial-use
rights. Review upstream terms for uses beyond this portfolio.

| Dataset | Records | Grain / fields |
|---|---:|---|
| stores.csv | 12 | Store ID/name; shared shelf and truck units; visit cost |
| skus.csv | 8 | SKU ID/name; unit cost, price, case pack, weekly holding cost |
| demand_forecast.csv | 384 | Store × SKU × week forecast units |
| opening_inventory.csv | 96 | Store × SKU opening units |
| dc_availability.csv | 32 | SKU × week DC release units |

## Original SHA-256 hashes

- `dc_availability.csv`: `56904cdbc47ff0a61c20bc10b14672dfe3eb80110ef2166db7cf3b37112c33de`
- `demand_forecast.csv`: `dcaa5dd08f4de2decb6dc4d12eb7eac96d796c51ba45fa538d0782c1eed31278`
- `opening_inventory.csv`: `d1851a67e5ffe0c3033d4aaa1e382cf5274443de002bc3271c19b3d1c1b743c5`
- `skus.csv`: `8a5b203dda12926e79087ac44fcc49fd71743432144da48f328074d860d1eb76`
- `stores.csv`: `c691079f918014bf1ce44c95861f600e1035291a4a54861ed3adfd79ede65672`
