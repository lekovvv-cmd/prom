const transliteration: Record<string, string> = {
  а: "a",
  б: "b",
  в: "v",
  г: "g",
  д: "d",
  е: "e",
  ё: "e",
  ж: "zh",
  з: "z",
  и: "i",
  й: "y",
  к: "k",
  л: "l",
  м: "m",
  н: "n",
  о: "o",
  п: "p",
  р: "r",
  с: "s",
  т: "t",
  у: "u",
  ф: "f",
  х: "h",
  ц: "ts",
  ч: "ch",
  ш: "sh",
  щ: "sch",
  ъ: "",
  ы: "y",
  ь: "",
  э: "e",
  ю: "yu",
  я: "ya",
};

/** Creates a stable technical identifier from the label a person sees. */
export function createSystemSlug(value: string): string {
  return Array.from(value.toLowerCase())
    .map(
      (character) =>
        transliteration[character] ??
        (/[a-z0-9]/.test(character) ? character : "_"),
    )
    .join("")
    .replace(/_+/g, "_")
    .replace(/^_+|_+$/g, "");
}
