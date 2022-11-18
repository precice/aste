#include <iostream>
#include <metis.h>
#include <vector>
extern "C" void partitionMetis(idx_t cell_count, idx_t point_count, idx_t *cellptr, idx_t *celldata, idx_t nparts, idx_t *point_partition);
extern "C" int  typewidth();

void partitionMetis(idx_t cell_count, idx_t point_count, idx_t *cellptr, idx_t *celldata, idx_t nparts, idx_t *point_partition)
{
  idx_t options[METIS_NOPTIONS];
  METIS_SetDefaultOptions(options);
  std::vector<idx_t> cell_partition(cell_count);
  idx_t              objval;
  // TODO: Check return value of the function (and potentially add an assert)
  METIS_PartMeshNodal(&cell_count, &point_count, cellptr, celldata, 0, 0, &nparts, 0, options, &objval, cell_partition.data(), point_partition);
}

int typewidth()
{
  return IDXTYPEWIDTH;
}
