import type { ReactElement } from "react";
import { Dialog } from "radix-ui";
import { describe, expect, test, vi } from "vitest";

import { Modal } from "./Modal";

type RootElement = ReactElement<{
  open: boolean;
  onOpenChange: (open: boolean) => void;
  children: ReactElement;
}>;

function renderModal(onClose = vi.fn()) {
  const element = Modal({
    title: "Test modal",
    children: <div>Content</div>,
    onClose,
  }) as RootElement;

  return { element, onClose };
}

describe("Modal", () => {
  test("uses the Radix dialog root as a controlled modal", () => {
    const { element, onClose } = renderModal();

    expect(element.type).toBe(Dialog.Root);
    expect(element.props.open).toBe(true);

    element.props.onOpenChange(false);
    expect(onClose).toHaveBeenCalledOnce();
  });

  test("does not close while the controlled dialog remains open", () => {
    const { element, onClose } = renderModal();

    element.props.onOpenChange(true);

    expect(onClose).not.toHaveBeenCalled();
  });

  test("renders content through a Radix portal", () => {
    const { element } = renderModal();

    expect(element.props.children.type).toBe(Dialog.Portal);
  });
});
