# Method decisions

Decided 17 Nov 2026. Each row is a choice I made, with the reason.

| Decision | Choice | Notes |
| --- | --- | --- |
| Launch sites | Egilsstaðir (65.28N, 14.40W), Keflavík (63.97N, 22.60W), New York stand-in (40.71N, 74.01W), Cambridge MA (42.36N, 71.09W), Juneau (58.30N, 134.42W) as control | New York point is a stand-in: WindBorne's real NY site location is not public. |
| Levels | 850, 500, 250 hPa | Roughly 1.5 km, 5.5 km, 10 km. |
| The gap | Grid cells more than 500 km from any IGRA2 station still reporting in 2026, inside 45 to 90N, 70W to 30E | 300 km and 800 km run as sensitivity checks only. |
| Horizons | 7 days (main) and 21 days (mean flight) | Two headline numbers. |
| Season | Every Dec to Feb day, winters 2013/14 to 2021/22 | About 800 launches per site. Shifted back one year (decided 17 Nov) because the WeatherBench2 ERA5 copy ends 10 Jan 2023, so 2022/23 is incomplete. |
| Pole handling | 3D (x, y, z) integrator, flies over the pole | Decided 17 Nov. The lat/lon integrator stopped about 12% of Egilsstaðir balloons past 88°N, which biased against Iceland. Tested on a rotation over the pole. |
| Steering bracket | Optimistic (hindsight, perfect next 6 h) and pessimistic (persistence, no look-ahead) pilots, both reported | Decided 17 Nov. WindBorne's real forecasts sit between the two. |
| Without 250 hPa | Sensitivity check with 850 and 500 hPa only (notebook 05) | Decided 17 Nov. 250 hPa is about FL340, inside the FL300 to FL400 band WindBorne no longer floats in since UA1093. Chosen over swapping to 150 hPa because GSB altitude limits aren't public. |
| Active stations | IGRA2 stations with last year 2026, plus Keflavík (63.97N, 22.60W) and Egilsstaðir (65.28N, 14.40W) added by hand | Decided 17 Nov. IGRA2 omits Keflavík and shows Egilsstaðir ending 2024, but AIP Iceland GEN 3.5 and ENR 5.3 say both still launch. Leaving them out would make Iceland look like a gap and flatter the Iceland result. |
