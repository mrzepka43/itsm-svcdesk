# ai-generated: 85% - GitHub Copilot wrote the explanation from the measured client and server percentiles
# Client/server latency gap

For the measurement, Toxiproxy sat between the load generator and svcdesk. Its
downstream latency toxic added 100 ms with 10 ms of jitter to each response. In
the 60-second open-loop run, oha measured a client p99 of 0.2135 seconds, while
the server histogram's p99 was 0.1079 seconds; the observed gap was 0.1056
seconds.

The server histogram starts timing when the HTTP request reaches the svcdesk
ASGI middleware and stops when svcdesk sends its response to the downstream
socket. The downstream proxy delay happens after that server-side observation,
so it is visible to oha but not included in the server histogram. The configured
100 ms delay explains most of the roughly 106 ms gap; the remaining few
milliseconds can come from proxy scheduling, network transport and the
distribution of the toxic's jitter. The comparison illustrates why a server
latency SLI alone does not measure the full time experienced by a client.
