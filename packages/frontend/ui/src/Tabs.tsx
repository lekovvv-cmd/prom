import { Tabs as RadixTabs } from "radix-ui";

export type TabItem = {
  content: React.ReactNode;
  label: string;
  value: string;
};

export function Tabs({
  defaultValue,
  items,
}: {
  defaultValue?: string;
  items: TabItem[];
}) {
  return (
    <RadixTabs.Root
      className="tabs"
      defaultValue={defaultValue ?? items[0]?.value}
    >
      <RadixTabs.List className="tabs-list">
        {items.map((item) => (
          <RadixTabs.Trigger
            className="tabs-trigger"
            key={item.value}
            value={item.value}
          >
            {item.label}
          </RadixTabs.Trigger>
        ))}
      </RadixTabs.List>
      {items.map((item) => (
        <RadixTabs.Content
          className="tabs-content"
          key={item.value}
          value={item.value}
        >
          {item.content}
        </RadixTabs.Content>
      ))}
    </RadixTabs.Root>
  );
}
