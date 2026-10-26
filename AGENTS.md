# Picasso repository guidance

This is an independent early SM7250 port. Read README.md, porting.toml and
docs/source-audit.md before editing. Use official UniXNU components and primary
vendor/hardware sources. Do not use other Picasso community ports as source or
evidence. Do not infer RAM from the 128 GB storage capacity.

The required target is iPhone X iOS 16 (currently pinned to 16.7.16/20H392),
not the official iPadOS 17 profile. Read docs/ios16.md. Darwin 22 source, driver
and prelink ABI qualification is pending. Preserve that explicit gate and do
not turn a Darwin 23 build or Apple input audit into an iOS 16 support claim.

Maintain format 2. Shared chip resources live under socs/sm7250; the local feed
is versioned with the device. Preserve source pins, upstream notices, component
IDs and runtime identifiers. Keep unqualified peripherals disabled. Do not
fabricate firmware paths, physical addresses, partition geometry or test results.

Update the affected porting.toml findings/evidence with code changes. Validate
using scripts/check-device.py, the official porting-record.py and the C++ timer
test. Complete kernel/package builds run in GitHub Actions. Host results and
device results are different milestones. Do not label an EFI application as a
firmware FD or a host kernel candidate as a boot image.

Image assembly remains gated until measured input requirements are met. There
are no device-write tools in this repository. Keep input images, device identity
and locally captured records under the ignored inputs/ directory.
