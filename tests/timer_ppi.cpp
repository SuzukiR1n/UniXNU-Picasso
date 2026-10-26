#include "ArmTimerPpi.h"
#include <cassert>

int main ()
{
  uint32_t cells[] = {1, 1, 0xff08, 1, 2, 0xff08, 1, 3, 0xff08, 1, 0, 0xff08};
  assert (armcpuVirtualTimerIntid (cells, 12) == 19);
  cells[7] = 11;
  assert (armcpuVirtualTimerIntid (cells, 12) == 27);
  cells[7] = 15;
  assert (armcpuVirtualTimerIntid (cells, 12) == 31);
  cells[7] = 16;
  assert (armcpuVirtualTimerIntid (cells, 12) == 0);
  cells[7] = 3;
  cells[6] = 0;
  assert (armcpuVirtualTimerIntid (cells, 12) == 0);
  assert (armcpuVirtualTimerIntid (cells, 9) == 0);
  assert (armcpuVirtualTimerIntid (nullptr, 12) == 0);
}
