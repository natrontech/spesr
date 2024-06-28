import { UpdateFilterEnum, updateDataStores } from "$lib/stores/data/load";

export const load = async () => {
  // Perform the existing data store update
  await updateDataStores({
    filter: UpdateFilterEnum.ALL
  }).catch((error) => {
    console.error(error);
  });
};
