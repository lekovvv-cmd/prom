const SHORT_RUSSIAN_WORDS =
  /(^|[\s([{«„"'])(а|в|во|да|до|и|из|к|ко|ли|на|не|но|о|об|обо|от|по|с|со|у|за|же|бы)\s+/giu;

export function keepShortRussianWords(text: string) {
  return text.replace(SHORT_RUSSIAN_WORDS, "$1$2\u00a0");
}
