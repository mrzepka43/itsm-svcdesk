---
svcdesk_decisions:
  C1: wallclock      # wallclock | business
  C2: immutable      # reopen | immutable
  C3: vip            # matrix | vip
---
<!-- ai-generated: 50% - ai supported me with chosing who should be service owner nad helped rewrite some of my simple text to more business like) -->

# Decisions

## C1 - SLA clock for P1

**Decision:** I've chosen wallclock for P1 tickets. Our clients' problems are real, and if one of this problems is urgent and touches critical part of their business, we have to do what we can to fix the issue as fast as possible. Of course our programmers will be paid extra for working overtime/on weekends.

**Rejected alternative:** Rejected only business wall clock for P1 priority. 

**Reason:** Our clients' problems are real, and if one of this problems is urgent and touches critical part of their business, we have to do what we can to fix the issue as fast as possible. Of course our programmers will be paid extra for working overtime/on weekends. There are many businesses works also on weekends, nad waiting for programmer if problem occurs friday 5pm, they will have to work 2 days with it.

**Service owner:** IT Service desk manager,  because P1 severity policy is owned by service operations and the SLA commitment is set at the service level.

**Customer outcome:** Reporter gets greater focus on the most important tickets, company can advertise that we care about our clients' most critical processes

## C2 - Closed tickets and reopening

**Decision:** We keep closed tickets immutable. After a ticket is resolved and then closed, the service refuses a reopen from the closed state and requires a new ticket for any follow-up work related to the same incident.

**Rejected alternative:** We reject the reopen-from-closed policy. Allowing a closed ticket to reopen would blur the distinction between a completed issue and a new issue, and it would make closed records less trustworthy for service reporting.

**Reason:** Creating a ticekt with relation to closed one creates a simple to read history of an issue, and reset SLA. New issue is spotted after client's tests, it's his responsibility to test thorough. Reopening a tickets creates a mess in programmer's task queue

**Service owner:** IT Service desk manager, it's their area of intrest, they want to keep it clean and structurized

**Customer outcome:** A Simple procedure for client, some bit of breathing room for the programmer after he closes the ticket

## C3 - VIP reporters and the priority matrix

**Decision:** We apply the VIP rule after matrix calculation. A VIP reporter who falls into P3 or P4 is promoted to P2, while P1 and P2 remain unchanged. This gives the desk a practical escalation mechanism without abandoning the base matrix.

**Rejected alternative:** We reject the matrix-only rule. If VIP status never changes the result, strategic customers could be under-prioritised simply because their urgency and impact values are not high enough in the baseline matrix.

**Reason:** VIP reporters represent materially important business relationships. The matrix is the default rule for everyday tickets, but the service desk needs a stronger escalation path for high-value customers whose issue may still deserve faster handling even when the plain matrix would place them at P3 or P4.

**Service owner:** Customer Support Lead; this role owns the escalation policy for VIP customers and prioritisation decisions that affect customer trust and service quality.

**Customer outcome:** VIP customers receive faster attention for issues that matter to the business even when their raw impact and urgency would otherwise be lower. This protects strategic relationships and keeps executive-level requests visible to the desk.
