import type { ReactElement } from "react";
import { describe, expect, test, vi } from "vitest";

import { Modal } from "./Modal";

type BackdropElement = ReactElement<{
  onClick: (event: unknown) => void;
  children: ReactElement<{
    children: ReactElement[];
  }>;
}>;

function renderModal(onClose = vi.fn()) {
  const element = Modal({
    title: "Test modal",
    children: <div>Content</div>,
    onClose
  }) as BackdropElement;

  return { element, onClose };
}

describe("Modal", () => {
  test("closes when backdrop is clicked", () => {
    const { element, onClose } = renderModal();
    const backdrop = {};

    element.props.onClick({ target: backdrop, currentTarget: backdrop });

    expect(onClose).toHaveBeenCalledOnce();
  });

  test("does not close when content is clicked", () => {
    const { element, onClose } = renderModal();
    const backdrop = {};
    const content = {};

    element.props.onClick({ target: content, currentTarget: backdrop });

    expect(onClose).not.toHaveBeenCalled();
  });

  test("wraps supplied content in the shared modal content region", () => {
    const { element } = renderModal();
    const dialog = element.props.children;
    const content = dialog.props.children[1] as ReactElement<{ className: string }>;

    expect(content.props.className).toBe("modal-content");
  });
});
