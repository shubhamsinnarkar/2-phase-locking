# 2-phase-locking

Rigorous 2 Phase Locking, with the wound-wait method for dealing with deadlock 

This requires that in addition to the lock being 2-Phase all Exclusive(X)
and Shared(S) Locks held by the transaction be released until after the transaction commits.
It guarantees strict schedules.
Rigorous 2PL has the property that for two conflicting transactions, their commit order
is their serializability order.
In Rigorous 2 PL, we can avoid deadlocks using multiple methods. Here, we will be using woundwait method.
This scheme basically checks the time stamp, and allows the younger transaction T to wait, but
when an older transaction requests an item held by a younger one, the older transaction forces
the younger one to abort and release the item. In both the cases, the transaction that enters
the system at a later stage is aborted
