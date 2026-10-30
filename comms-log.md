---
lab4_comms:
  awareness: 2026-10-12T05:06:19Z
  detection: 2026-10-12T05:06:19Z
  classification: 2026-10-12T05:08:19Z
  nis2:
    early_warning_due: 2026-10-13T05:06:19Z
    notification_due: 2026-10-15T05:06:19Z
    notification_sent: 2026-10-12T06:00:00Z
    final_report_due: 2026-11-12T06:00:00Z
  ksc:
    early_warning_due: 2026-10-13T05:06:19Z
    notification_due: 2026-10-15T05:06:19Z
    notification_sent: 2026-10-12T06:00:00Z
    final_report_due: 2026-11-12T06:00:00Z
  dora:
    initial_due: 2026-10-12T09:08:19Z
    initial_sent: 2026-10-12T05:30:00Z
    intermediate_due: 2026-10-15T05:30:00Z
    intermediate_sent: 2026-10-14T08:00:00Z
    final_due: 2026-11-14T08:00:00Z
  log:
    - {at: 2026-10-12T05:30:00Z, to: "financial supervisor", what: "Hypothetical DORA initial notification after provisional major-incident classification"}
    - {at: 2026-10-12T06:00:00Z, to: "CSIRT and relevant NIS2 authority", what: "Hypothetical KSC and NIS2 incident notifications"}
    - {at: 2026-10-14T08:00:00Z, to: "financial supervisor", what: "Hypothetical DORA intermediate report"}
    - {at: 2026-11-12T06:00:00Z, to: "NIS2 authority and CSIRT", what: "Hypothetical NIS2 and KSC final reports"}
    - {at: 2026-11-14T08:00:00Z, to: "financial supervisor", what: "Hypothetical DORA final report"}
---
<!-- ai-generated: 65% - Copilot calculated report deadlines from the declared assumptions and course rules -->

# Communications log: the regulators' clocks

## The three instants you defend

For this exercise I use 05:06:19Z as both detection and organizational awareness: that is the recorded start of the P1 `ShopCheckoutSlow` alert and the first documented point at which the on-call had evidence of a significant checkout impact. The ticket was acknowledged at 05:06:56Z. I use 05:08:19Z for DORA classification because the detecting alert's firing run had ended by then, giving the on-call a bounded incident window to assess; this is a hypothetical exercise assumption, not a legal determination.

## The log

All communications below are hypothetical submissions calculated for the exercise, not reports that were actually sent. The initial DORA notification is scheduled for 05:30Z on 12 October, before its 09:08:19Z deadline. NIS2 and KSC notifications are scheduled for 06:00Z that day, well before their respective 72-hour deadlines. The intermediate DORA report is scheduled for 08:00Z on 14 October, before its 72-hour deadline; the final reports are scheduled one calendar month after their respective notifications.
