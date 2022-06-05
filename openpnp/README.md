# OpenPnP Scripts

Files in this directory should be copied into your $HOME/.openpnp2/Scripts directory.

## create-feeders.py

This script will create multiple slotted feeders (ReferenceSlotAutoFeeder) which can
be configured once and used for multiple parts simply by updating the feeder
assignment for the slot.

## scan-feeders-for-part-labels.py

This script attempts to scan a part label for each defined feeder. If a part label
is successfully read in and a part matches that label the feeder will be updated to
provide that part if it isn't already. In the case of a slotted feeder
(ReferenceSlotAutoFeeder, SlotSchultzFeeder), the assigned feeder for the slot will
be updated with a feeder that provides that part.

If no part label can be read or the label does not match a defined part the feeder
can optionally be disabled.
