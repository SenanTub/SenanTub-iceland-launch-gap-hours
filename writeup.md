# What one Iceland launch buys

Senan Tubridy · Boston · November 2026
Code, notebooks and an interactive replay: github.com/SenanTub/iceland-launch-gap-hours

**Short answer: less than I thought.** Per launch, a balloon from Iceland spends less time over the thinly observed North Atlantic than one from the northeastern US. That holds whether it drifts or steers, with the gap set at 500 or 800 km. Iceland's one real edge is the Arctic, where steered balloons get about 1.2 to 1.5 times the hours a US balloon does. So I'd take back the gap-filling part of my Iceland proposal.

## Why I asked

Iceland is on your list for new sites [1], and I argued for it. But your balloons from existing sites already reach the Arctic [2]. So the fair question was what one Iceland launch adds.

I measured it as **gap-hours**: the hours a balloon spends more than 500 km from any active radiosonde station, inside 45 to 90°N and 70°W to 30°E. That's about a quarter of the box.

## How I did it

- **Winds:** ERA5 reanalysis [3] at 1.5°, every 6 hours, from the WeatherBench 2 copy [4].
- **Launches:** one virtual balloon a day from each site, every winter day from December 2013 to February 2022. That's 812 launches per site. Each one flies 21 days, your average flight [5].
- **Sites:** Egilsstaðir, Keflavík, Cambridge MA, a stand-in New York point, and Juneau as a control.
- **Stations:** NOAA's IGRA2 list [6]. Keflavík and Egilsstaðir are added from the Icelandic AIP [7], because IGRA2 leaves them out, and leaving them out would have flattered Iceland.
- **Integrator:** RK4 on the sphere with 1-hour steps. I tested it against an exact solid-body rotation [8], including a path over the pole. Halving the step cuts the error 16 times, as it should for a 4th-order method.
- **Drifting:** at 500 hPa.
- **Steered:** between 850 and 500 hPa every 6 hours. I left out 250 hPa because it's inside the FL300 to FL400 band you no longer float in [9]. The steering is bracketed by two simple pilots. One knows the next 6 hours of wind exactly; the other assumes the wind won't change. Your forecasts sit somewhere between them.

## Results

Median gap-hours per launch over 21 days, 500 km gap.

| | Egilsstaðir | Keflavík | New York* | Cambridge | Juneau |
| --- | --- | --- | --- | --- | --- |
| Drifting at 500 hPa | 12 | 14 | 18 | 20 | 21 |
| Steered (no look-ahead to perfect look-ahead) | 35 to 40.5 | 40 to 44.5 | 48 to 54 | 53 | 53 to 54 |
| Balloons in the gap at any moment, per daily launch, steered [10] | 2.0 to 2.2 | 2.3 to 2.4 | 2.5 to 2.7 | 2.7 to 2.8 | 2.7 |

\*New York is a stand-in point (40.71°N, 74.01°W); your site's location isn't public.

## What I found

1. **US launches already run through the gap.** A drifting Cambridge balloon reaches it after a median of 23 hours and spends 20 hours in it. One from Egilsstaðir takes about 50 hours to get there and spends 12. Iceland is ringed by stations, and its balloons mostly drift east over Norway, which is well covered (Figure 1).
2. **How the balloon flies matters more than where it starts.** Steering lifts gap-hours 2.5 to 3.4 times at every site. Even so, both Iceland sites rank fourth or fifth at 500 and 800 km under both pilots. So the result doesn't depend on forecast skill (Figure 2).
3. **Iceland's edge is the Arctic.** Over 8 in 10 steered Iceland launches reach the gap north of 60°N, against about 7 in 10 from the US. That gives them 30 to 35 Arctic hours per launch, against 23 to 25. It's real, but modest. I looked at this split after seeing the main result.

## Where it breaks

- The gap counts radiosondes only. Aircraft, satellites and your own fleet aren't in it.
- Each site is judged alone, not against the fleet you already fly.
- The pilots are stand-ins: three heights, instant height changes and unlimited ballast.
- With a looser 300 km gap, Keflavík moves into the top three. The ranking depends on the definition.
- Launch weather, airspace and logistics are separate questions, covered in the proposal.

## What would settle it

Your flight logs. The same method run on your real tracks, and against your real fleet, would answer this properly. I'd be glad to do that.

How this was made: Claude wrote the code to my spec. I chose the method, checked it, and wrote down where it breaks.

## References

1. WindBorne Systems, Field Operations Specialist job posting, 5 June 2026. jobs.khoslaventures.com/companies/windborne-systems-2/jobs/81743212-field-operations-specialist
2. Spisak et al. (2026). arXiv:2602.02714.
3. Hersbach, H. et al. (2020). The ERA5 global reanalysis. *Q. J. R. Meteorol. Soc.* 146, 1999 to 2049.
4. Rasp, S. et al. (2024). WeatherBench 2: a benchmark for the next generation of data-driven global weather models. *J. Adv. Model. Earth Syst.* 16. Data: gs://weatherbench2/datasets/era5/1959-2023_01_10-6h-240x121_equiangular_with_poles_conservative.zarr
5. WindBorne balloon launch at MIT, event page, November 2026. luma.com/fdlorche
6. Durre, I. et al. (2018). Enhancing the data coverage in the Integrated Global Radiosonde Archive. *J. Atmos. Oceanic Technol.* 35, 1753 to 1770. Station list: ncei.noaa.gov/pub/data/igra/igra2-station-list.txt (downloaded 17 Nov 2026)
7. AIP Iceland, GEN 3.5 (meteorological services) and ENR 5.3 (balloon launch sites). Isavia ANS.
8. Williamson, D. L. et al. (1992). A standard test set for numerical approximations to the shallow water equations in spherical geometry. *J. Comput. Phys.* 102, 211 to 224 (test case 1).
9. WindBorne Systems, UA1093 update. lb.windbornesystems.com/blog/ua1093-update
10. Little, J. D. C. (1961). A proof for the queuing formula L = λW. *Operations Research* 9, 383 to 387. Balloons in the gap = launches per day × mean gap-hours per launch ÷ 24, assuming 21-day flights.

Coastlines: Natural Earth (public domain).
