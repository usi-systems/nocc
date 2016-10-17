# Gotthard

Network latency can have a significant impact on the performance of
transactional storage systems, particularly in wide area or geo-distributed
deployments. To reduce latency, systems typically rely on a cache to service
read-requests closer to the client. However, caches are not effective for
write-heavy workloads, which have to be processed by the storage system in order
to maintain serializability.

Gotthard is a new system designed to reduce network latency
for write-heavy workloads.  Gotthard leverages recent advances in network data
plane programmability to execute transaction processing logic directly in
network devices. Specifically, Gotthard examines network traffic to observe and
log transaction requests. If Gotthard suspects that a transaction is likely to
be aborted at the store, it optimistically aborts the transaction by re-writing
the packet header, and routing the packets back to the client. As a result,
Gotthard can significantly reduce the overall latency for processing a
request. Moreover, since requests are processed "on the wire", Gotthard
reduces load on the storage server, increasing transaction throughput.

