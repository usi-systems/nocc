# NOCC

Optimistic concurrency control (OCC) is inefficient for highcontention
workloads. When concurrent transactions conflict,
an OCC system wastes CPU resources verifying transactions,
only to abort them. This paper presents a new system,
called Network Optimistic Concurrency Control (NOCC),
which reduces load on storage servers by identifying transactions
that will abort as early as possible, and aborting them
before they reach the store. NOCC leverages recent advances
in network data plane programmability to speculatively execute
transaction verification logic directly in network devices.
NOCC examines network traffic to observe and log transaction
requests. If NOCC suspects that a transaction is likely
to be aborted at the store, it aborts the transaction early by
re-writing the packet header, and routing the packets back to
the client. For high-contention workloads, NOCC improves
transaction throughput, and reduces server load.
