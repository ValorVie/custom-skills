import { Box } from "ink";
import { ActionBar } from "../components/ActionBar";
import { FilterBar } from "../components/FilterBar";
import { Header } from "../components/Header";
import { ResourceList } from "../components/ResourceList";
import { TabBar } from "../components/TabBar";
import type {
  Resource,
  SourceFilter,
  Target,
  TypeFilter,
} from "../hooks/useResources";

interface MainScreenProps {
  target: Target;
  targets: Target[];
  typeFilter: TypeFilter;
  sourceFilter: SourceFilter;
  selectedCount: number;
  resources: Resource[];
  selectedIndex: number;
}

export function MainScreen({
  target,
  targets,
  typeFilter,
  sourceFilter,
  selectedCount,
  resources,
  selectedIndex,
}: MainScreenProps) {
  return (
    <Box flexDirection="column">
      <Header
        target={target}
        total={resources.length}
        selected={selectedCount}
      />
      <TabBar current={target} targets={targets} />
      <FilterBar typeFilter={typeFilter} sourceFilter={sourceFilter} />
      <ResourceList resources={resources} selectedIndex={selectedIndex} />
      <ActionBar />
    </Box>
  );
}
