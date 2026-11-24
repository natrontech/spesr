import { Tabs as TabsPrimitive } from "bits-ui";
import Content from "./tabs-content.svelte";
import Trigger from "./tabs-trigger.svelte";
import List, { tabsListVariants, type TabsListVariant } from "./tabs-list.svelte";

const Root = TabsPrimitive.Root;

export {
  Root,
  Content,
  List,
  Trigger,
  tabsListVariants,
  type TabsListVariant,
  Root as Tabs,
  Content as TabsContent,
  List as TabsList,
  Trigger as TabsTrigger
};
