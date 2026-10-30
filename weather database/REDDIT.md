# Reddit as a source-discovery channel

Checked 2026-10-30. Reddit is useful for finding hypotheses, unfamiliar operational terms, data portals and counterexamples. It does not establish a causal effect, representative frequency or sufficient condition for Frankfurt's operating direction or runway 18 availability. Self-described pilots/controllers are not verified experts merely because they post in a specialist subreddit.

## Leads actually inspected

| Thread | What it contributes | Verification status and next source |
|---|---|---|
| [r/ATC: NYC area / ZNY delays](https://www.reddit.com/r/ATC/comments/1max5qr/nyc_area_zny_delays/) | A discussion of apparently clear local weather despite delays; hypotheses include route deviations, congested sectors and staffing interacting with weather. | The [FAA weather-delay FAQ](https://www.faa.gov/nextgen/programs/weather/faq) independently describes capacity/demand interactions and en-route weather. It does not verify the particular incident or commenters' staffing claims. |
| [r/datasets: flight cancellation/delay/status data](https://www.reddit.com/r/datasets/comments/w7xz4p/free_flights_cancellationdelaysstatus_dataset/) | A pointer to a FAA integrated-terminal-weather catalog entry. | The linked old catalog URL returned 404 during our check. This is a discovery lead, not an accessible downloaded dataset. Continue from the current [FAA data portal](https://www.faa.gov/data). |
| [r/aviation: 35 years of flight data](https://www.reddit.com/r/aviation/comments/1d3mf1b/35_years_of_faa_flight_data_query_with_natural/) | Example questions and a third-party SQL demonstration. | The post's “FAA” title does not establish dataset provenance. Verify against BTS/FAA original tables before reusing any numbers. The linked demonstration was not audited. |

These were targeted examples, not a systematic or exhaustive Reddit sample. The r/ATC page had collapsed reply branches; this review does not claim to have read every comment. No messages or posts were sent.

## How a lead enters the evidence base

1. Record the public thread link and one testable claim, without treating votes or apparent professional identity as validation.
2. Find its original source: operational bulletin, weather observation, airport record, paper or dataset.
3. Specify the relevant output and time relationship. A weather-delayed flight is not evidence that Frankfurt switched direction or closed runway 18.
4. Test the condition on appropriate data, including counterexamples and a held-out period. Promote only the corroborated claim into the findings.

For example, “remote thunderstorms can delay arrivals while local wind remains favorable” suggests separating network disruption from local runway-state labels. It does not justify a rule that arrival delays imply a direction change.

## Product and research access

No Reddit data feed or bulk collection has been configured. Public browsing is not proof that a continuously operating API or redistributable training corpus is available. Reddit's current [developer-access guidance](https://support.reddithelp.com/hc/en-us/articles/14945211791892-Developer-Platform-Accessing-Reddit-Data) distinguishes approved API access from its academic research program. Verify the appropriate access route before making Reddit a product dependency. Our current deliverable is a small source-discovery note with links, not a mirrored Reddit corpus.
