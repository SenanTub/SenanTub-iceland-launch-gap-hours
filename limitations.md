# Limitations (for the README and write-up)

Collected 17 Nov 2026. Each limitation names the notebook where it applies.

## The question and its definitions
- **"The gap" is a definition, not a fact.** Main version: more than 500 km from any active radiosonde station, inside 45 to 90°N and 70°W to 30°E. Results are also shown at 300 and 800 km (notebooks 02, 04). The site ranking changes between 300 km and 500/800 km, so the answer depends on the definition.
- **Gap-hours count only radiosonde stations.** Aircraft reports, satellites and other balloons (including WindBorne's own fleet) are ignored. A place 600 km from a radiosonde can still be well observed by other means.
- **Two cuts were added after seeing the main result:** widening the box to 90°E (notebook 03) and splitting the gap at 60°N into Atlantic and Arctic parts (notebooks 03, 04). They're labelled as follow-ups, not headlines.
- **Each site is judged on its own.** We don't model WindBorne's existing fleet, so we can't say how much of an Iceland balloon's gap time some other balloon already covers.

## Stations
- **IGRA2 doesn't match what Iceland actually launches.** It omits Keflavík and shows Egilsstaðir stopping in 2024, but AIP Iceland (GEN 3.5, ENR 5.3) says both still launch. Both were added by hand (decisions.md). Leaving them out would have flattered Iceland.
- **"Active" means IGRA2's last year of data is 2026.** Stations that report irregularly, or that stopped part way through 2026, may be misclassified.
- **Egilsstaðir launches only from 1 Sep to 10 May.** It's treated as active all winter, which is correct for Dec to Feb.

## Winds and data
- **ERA5 reanalysis at 1.5°, every 6 hours** (WeatherBench2 copy). It's coarse for exact routes, but fine for drift over days on the scale of weather systems.
- **Winters 2013/14 to 2021/22,** because this copy of the data ends on 10 Jan 2023. Winter only (Dec to Feb launches); summer isn't tested.
- **The New York site is a stand-in** (40.71°N, 74.01°W). WindBorne's real site isn't public.
- **Launch-weather risk isn't modelled here.** Every launch is assumed to go ahead. The separate ERA5 launch-weather table in the Iceland doc covers that.

## Flight model
- **Balloons float at fixed pressure levels (850, 500, 250 hPa).** Real balloons float at any height in their range.
- **Every flight lasts exactly 21 days** (the mean flight on the MIT event page). There are no early terminations or recoveries.
- **250 hPa is about 34,000 ft (FL340).** Since the UA1093 incident, WindBorne balloons no longer hold neutral buoyancy between FL300 and FL400. The passive 250 hPa runs, and steering that uses 250 hPa, describe a height WindBorne now avoids holding. Notebook 05 reruns the steering with 850 and 500 hPa only. Iceland stays last or fourth at 500 and 800 km. Egilsstaðir's good showing at 300 km disappears, because it came from 250 hPa.
- **We don't know WindBorne's real altitude range,** including whether GSBs float as low as 850 hPa (about 5,000 ft). The heights are standard pressure levels, not taken from flight logs.
- **Pole handling:** the brief's lat/lon integrator stops balloons past 88°N. It would have stopped about 12% of Egilsstaðir balloons at 500 hPa, and those lost hours count against Iceland. We use a 3D (x, y, z) integrator instead. It was tested on a rotation over the pole, where it converges at 4th order. Notebook 02 shows the old method changes Iceland's 21-day median by 1 to 3 hours.

## Steering (notebook 04)
- **Neither pilot is WindBorne's navigation.** The two pilots bracket it: an optimistic one using hindsight (the real winds of the next 6 hours), and a pessimistic one using persistence (the current winds, assumed frozen for 6 hours). The comparison between sites is fair because every site gets the same pilot. The absolute hours are not predictions.
- **Neither is a strict bound.** Both are greedy and only look 6 hours ahead. A short-sighted pilot can do worse than one with less information, or worse than holding one good height.
  - For Cambridge, the "stay" rule did worse than holding 850 hPa.
  - In one test winter, Egilsstaðir did better with persistence than with hindsight.
- **The tie-break rule matters.** "Stay" (the brief's rule) and "closest" give quite different hours. Both are shown.
- **Only three heights; instant height changes; unlimited ballast and gas.** Real height changes take time and use up finite ballast or lift gas.
- **The pilot knows exactly where the gap is** and steers only for gap-hours. A real pilot also balances airspace, ballast, recovery and customers.
- **Persistence assumes the wind at every height stays frozen for 6 hours.** In reality systems move. Near jets and fronts, the wind can change a lot in 6 hours. It also treats the reanalysis at decision time as "what the pilot knows", whereas a real analysis arrives late and is less exact.

- **Open question:** with the "closest" rule, every site spends about 60/20/20% of its time at 850/500/250 hPa, under both pilots. Choices vary by site, winter and decision time, and most decisions (about 84%) are made outside the gap, where 850 hPa is picked most often. No bug was found, but the reason for the near-identical totals isn't fully explained.

## Fleet scaling
- **Little's law (balloons in the gap = launches per day × mean gap-hours per launch ÷ 24)** assumes steady daily launches and fixed 21-day flights.
