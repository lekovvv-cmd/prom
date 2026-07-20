import { describe, expect, it } from "vitest";

import type {
  ServiceDeskCategory,
  ServiceDeskService,
} from "../../../entities/service-desk-catalog/model/types";
import {
  buildRoutingCategoryOptions,
  buildRoutingServiceOptions,
} from "./ServiceDeskAdminRoutingPage";

const categories: ServiceDeskCategory[] = [
  {
    id: "category-2",
    title: "Учебный процесс",
    description: null,
    parent_id: null,
    position: 0,
    is_active: true,
    deleted_at: null,
  },
  {
    id: "category-1",
    title: "Администрирование",
    description: null,
    parent_id: null,
    position: 0,
    is_active: true,
    deleted_at: null,
  },
];

const services: ServiceDeskService[] = [
  {
    id: "service-2",
    category_id: "category-2",
    title: "Перенос занятия",
    short_description: null,
    description: null,
    position: 0,
    is_active: true,
    deleted_at: null,
    category: null,
  },
  {
    id: "service-1",
    category_id: "category-1",
    title: "Заказ воды",
    short_description: null,
    description: null,
    position: 0,
    is_active: true,
    deleted_at: null,
    category: categories[1],
  },
];

describe("routing condition catalog options", () => {
  it("shows category names instead of identifiers", () => {
    expect(buildRoutingCategoryOptions(categories)).toEqual([
      { value: "category-1", label: "Администрирование" },
      { value: "category-2", label: "Учебный процесс" },
    ]);
  });

  it("shows service names together with their category", () => {
    expect(buildRoutingServiceOptions(services, categories)).toEqual([
      { value: "service-1", label: "Заказ воды · Администрирование" },
      { value: "service-2", label: "Перенос занятия · Учебный процесс" },
    ]);
  });
});
