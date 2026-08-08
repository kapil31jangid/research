export function humanize(value: string): string {
  return value
    .replaceAll("_", " ")
    .replace(/\b\w/g, (letter) => letter.toUpperCase());
}

const misconceptionLabels: Record<string, string> = {
  adds_denominators: "Adding denominators directly",
  subtracts_denominators: "Subtracting denominators directly",
  larger_denominator_larger_fraction: "Comparing by denominator size alone",
  fails_equivalence: "Changing only one part of an equivalent fraction",
  incorrect_common_denominator: "Choosing a denominator that is not shared",
  confuses_numerator_denominator: "Mixing up numerator and denominator",
  mixed_improper_conversion: "Converting mixed numbers without equal parts",
  incorrect_cancelling: "Dividing only one part of a fraction",
};

export function humanizeMisconception(value: string): string {
  return misconceptionLabels[value] ?? humanize(value);
}

export function percent(value: number): string {
  return `${Math.round(value * 100)}%`;
}

export function latency(value: number | undefined): string {
  return value === undefined ? "—" : `${value.toFixed(2)} ms`;
}

export function greeting(): string {
  const hour = new Date().getHours();
  if (hour < 12) return "Good morning";
  if (hour < 18) return "Good afternoon";
  return "Good evening";
}
