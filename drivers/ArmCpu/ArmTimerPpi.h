// SPDX-License-Identifier: BSD-2-Clause-Patent
#ifndef UNIXNU_ARM_TIMER_PPI_H
#define UNIXNU_ARM_TIMER_PPI_H

#include <stdint.h>

// ADT cells are little-endian on this ARM64 target. The architectural timer
// binding orders secure, nonsecure physical, virtual, and hypervisor IRQs.
// Return zero for malformed data, an SPI, or an out-of-range PPI.
static inline uint32_t armcpuVirtualTimerIntid (const uint32_t *cells, unsigned count)
{
  if (cells == nullptr || count != 12 || cells[6] != 1 || cells[7] > 15) { return 0; }
  return 16 + cells[7];
}

#endif
